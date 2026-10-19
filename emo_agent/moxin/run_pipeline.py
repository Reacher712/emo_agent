import argparse
import base64
import csv
import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, quote, urlparse

import requests

from emollm_infer import infer_emotion
from prompt_selector import select_template
from project_paths import MODEL_DIR, PROMPT_CSV, LOG_CSV, OUTPUT_DIR, DELIVERABLES_DIR, load_project_env

try:
    from dotenv import load_dotenv  # optional
except Exception:  # pragma: no cover
    load_dotenv = None


DEFAULT_MODEL_DIR = MODEL_DIR
DEFAULT_PROMPT_CSV = PROMPT_CSV
DEFAULT_LOG_CSV = LOG_CSV
DEFAULT_OUTPUT_DIR = OUTPUT_DIR
DEFAULT_DELIVERABLES_DIR = DELIVERABLES_DIR


def _load_env() -> None:
    load_project_env()


def _next_test_id(log_csv: Path, prefix: str) -> str:
    if not log_csv.exists():
        return f"{prefix}-001"
    max_num = 0
    with log_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = str(row.get("test_id", "")).strip()
            if tid.startswith(prefix + "-"):
                try:
                    max_num = max(max_num, int(tid.split("-")[1]))
                except Exception:
                    pass
    return f"{prefix}-{max_num + 1:03d}"


def _append_log(log_path: Path, row: Dict[str, str]) -> None:
    headers = [
        "test_id",
        "test_time",
        "module",
        "test_case",
        "input_summary",
        "status",
        "latency_ms",
        "output_path",
        "error_message",
        "operator",
        "notes",
    ]
    file_exists = log_path.exists()
    with log_path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _canonical_query(params: Dict[str, str]) -> str:
    items = sorted((k, v) for k, v in params.items() if v is not None and str(v) != "")
    return "&".join(f"{quote(str(k), safe='-_.~')}={quote(str(v), safe='-_.~')}" for k, v in items)


def _build_volc_headers(
    *,
    access_key_id: str,
    secret_access_key: str,
    host: str,
    method: str,
    canonical_uri: str,
    query_params: Dict[str, str],
    body_str: str,
    region: str,
    service: str,
) -> Dict[str, str]:
    x_date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short_date = x_date[:8]
    payload_hash = _sha256_hex(body_str)
    canonical_querystring = _canonical_query(query_params)
    canonical_headers = f"host:{host}\n" f"x-content-sha256:{payload_hash}\n" f"x-date:{x_date}\n"
    signed_headers = "host;x-content-sha256;x-date"
    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )
    credential_scope = f"{short_date}/{region}/{service}/request"
    string_to_sign = "HMAC-SHA256\n" f"{x_date}\n" f"{credential_scope}\n" f"{_sha256_hex(canonical_request)}"
    k_date = _hmac_sha256(secret_access_key.encode("utf-8"), short_date)
    k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"request", hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = (
        "HMAC-SHA256 "
        f"Credential={access_key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    return {
        "Host": host,
        "Content-Type": "application/json",
        "X-Date": x_date,
        "X-Content-Sha256": payload_hash,
        "Authorization": authorization,
    }


def _deep_get_first(node: Any, keys: list[str]) -> Any:
    key_set = {k.lower() for k in keys}
    queue = [node]
    while queue:
        cur = queue.pop(0)
        if isinstance(cur, dict):
            for k, v in cur.items():
                if str(k).lower() in key_set:
                    return v
                queue.append(v)
        elif isinstance(cur, list):
            queue.extend(cur)
    return None


def _sanitize_case_name(raw: str) -> str:
    safe = re.sub(r"[^\w\-]+", "_", raw.strip(), flags=re.UNICODE).strip("_")
    return safe[:80] if safe else "case"


def _archive_case(deliverables_root: Path, case_name: str, file_paths: list[Path], log_path: Path) -> Path:
    case_dir = deliverables_root / _sanitize_case_name(case_name)
    case_dir.mkdir(parents=True, exist_ok=True)
    for p in file_paths:
        if p.exists():
            shutil.copy2(p, case_dir / p.name)
    if log_path.exists():
        shutil.copy2(log_path, case_dir / log_path.name)
    return case_dir


def _render_music_prompt(emotion: Dict[str, Any], template: Dict[str, str], duration_sec: int | None = None) -> str:
    style = str(emotion.get("music_profile", {}).get("style", "")).strip() or str(template.get("style", "")).strip() or "calm_piano"
    duration = duration_sec if duration_sec is not None else int(emotion.get("music_profile", {}).get("duration_sec", 120))
    label = str(emotion.get("emotion_label", "平静"))
    return f"{label}情绪疗愈背景纯音乐，风格{style}，时长{duration}秒，旋律自然平稳"


def _build_soothing_response(emotion: Dict[str, Any], template: Dict[str, str]) -> Dict[str, str]:
    label = str(emotion.get("emotion_label", "平静"))
    intensity = int(emotion.get("intensity", 2))
    guide_text = str(emotion.get("guide_text", "")).strip()
    imagery = str(template.get("imagery_keywords", "")).strip()

    empathy_map = {
        "焦虑": "我感受到你现在有些紧绷和不安，这种状态在高负荷阶段很常见。",
        "压力": "你在承担很多任务，这种被事务挤压的感觉并不说明你不够好。",
        "低落": "你现在的情绪有些下沉，这种低能量阶段同样值得被认真照顾。",
        "平静": "你已经在向稳定状态靠近，这种平和感很宝贵。",
        "积极": "你现在有不错的积极能量，这是继续稳步前进的好时机。",
    }
    explain_map = {
        "焦虑": "我们先通过“低刺激画面+舒缓节律”降低神经系统唤醒水平，再逐步把注意力拉回当下。",
        "压力": "先用视觉留白和稳定节拍减轻认知负荷，帮助你从“连续任务模式”切回“可恢复模式”。",
        "低落": "先通过柔和意象和慢节奏音乐提供情绪托底，再慢慢恢复心理能量。",
        "平静": "继续维持低刺激与稳定节律，有助于把这份平静转化为可持续状态。",
        "积极": "通过更清晰的意象和有序节律巩固积极状态，避免波动回落。",
    }
    action_map = {
        "焦虑": "先做3轮“吸气4秒-呼气6秒”的呼吸，再把注意力放在画面中的一个固定意象上持续30秒。",
        "压力": "先暂停手头任务1分钟，跟随音乐做慢呼吸，并只给自己设定下一步最小动作。",
        "低落": "请先完成一次60秒的呼吸放松，再用一句话描述此刻最真实的感受。",
        "平静": "保持当前节奏，听完整段音乐后记录1条让你稳定下来的触发因素。",
        "积极": "趁当前状态做一个15分钟的小目标，并在音乐结束后快速复盘完成度。",
    }

    empathy = empathy_map.get(label, "你的感受是有效的，我们会一起把状态慢慢拉回到更可控的区间。")
    explanation = explain_map.get(label, "系统会使用匹配你当前情绪的国画与音乐，帮助你逐步稳定状态。")
    action = action_map.get(label, "先做三次缓慢呼吸，然后把注意力聚焦到一个具体感受上。")

    if guide_text:
        action = f"{action} {guide_text}"
    if imagery:
        explanation = f"{explanation} 本次意象重点为：{imagery}。"

    full_text = f"{empathy}\n{explanation}\n建议：{action}\n当前识别：{label}（{intensity}/5）"
    return {
        "empathy": empathy,
        "explanation": explanation,
        "action": action,
        "full_text": full_text,
    }


def _sd_txt2img(api_url: str, positive: str, negative: str, width: int, height: int, steps: int, cfg_scale: float, out_file: Path, seed: int = -1, checkpoint: str = "sd_xl_base_1.0.safetensors", lora: str = "landscape-painting-sdxl_v2 (1)") -> Dict[str, Any]:
    endpoint = api_url.rstrip("/") + "/sdapi/v1/txt2img"
    payload = {
        "prompt": f"{positive} <lora:{lora}:0.7>" if lora else positive,
        "negative_prompt": negative,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "sampler_name": "DPM++ 2M",
        "scheduler": "Karras",
        "seed": seed,
        "override_settings": {"sd_model_checkpoint": checkpoint},
    }
    resp = requests.post(endpoint, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    images = data.get("images") or []
    if not images:
        raise RuntimeError("SD API 返回为空，未生成图片")
    out_file.write_bytes(base64.b64decode(images[0]))
    info = data.get("info") or {}
    if isinstance(info, str):
        info = json.loads(info)
    metadata = {"backend": "webui", "checkpoint": checkpoint, "lora": lora, "requested_parameters": payload, "actual_info": info}
    out_file.with_suffix(".metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def _music_submit_and_query(prompt: str, duration_sec: int, wait_sec: int, poll_sec: int, download_audio: bool, out_dir: Path) -> Dict[str, str]:
    _load_env()
    auth_mode = os.getenv("MUSIC_AUTH_MODE", "volc_aksk").strip()
    submit_url = os.getenv("MUSIC_API_SUBMIT_URL", "").strip()
    query_url = os.getenv("MUSIC_API_QUERY_URL", "").strip()
    api_key = os.getenv("MUSIC_API_KEY", "").strip()
    access_key_id = os.getenv("VOLC_ACCESS_KEY_ID", "").strip()
    secret_access_key = os.getenv("VOLC_SECRET_ACCESS_KEY", "").strip()
    host = os.getenv("MUSIC_API_HOST", "open.volcengineapi.com").strip()
    action = os.getenv("MUSIC_API_ACTION", "GenBGMForTime").strip()
    api_version = os.getenv("MUSIC_API_VERSION", "2024-08-12").strip()
    region = os.getenv("MUSIC_API_REGION", "cn-beijing").strip()
    service = os.getenv("MUSIC_API_SERVICE", "imagination").strip()
    api_model_version = os.getenv("MUSIC_API_MODEL_VERSION", "v5.0").strip()

    submit_payload: Dict[str, Any] = {
        "Text": prompt,
        "Duration": duration_sec,
        "Version": api_model_version,
    }
    submit_body = json.dumps(submit_payload, ensure_ascii=False, separators=(",", ":"))
    query_params = {"Action": action, "Version": api_version}
    if not submit_url:
        submit_url = f"https://{host}/?{_canonical_query(query_params)}"
    if not query_url:
        query_url = f"https://{host}/?Action=QuerySong&Version={api_version}"

    if auth_mode == "bearer":
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    else:
        headers = _build_volc_headers(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            host=host,
            method="POST",
            canonical_uri="/",
            query_params=query_params,
            body_str=submit_body,
            region=region,
            service=service,
        )

    submit_resp = requests.post(submit_url, headers=headers, data=submit_body.encode("utf-8"), timeout=90)
    submit_resp.raise_for_status()
    submit_json = submit_resp.json()
    task_id = _deep_get_first(submit_json, ["TaskID", "TaskId"])
    if not task_id:
        raise RuntimeError(f"音乐提交成功但未拿到TaskID: {submit_json}")
    task_id = str(task_id)

    parsed = urlparse(query_url)
    query_qs = parse_qs(parsed.query)
    query_params_sign = {
        "Action": (query_qs.get("Action", ["QuerySong"])[0] or "QuerySong"),
        "Version": (query_qs.get("Version", ["2024-08-12"])[0] or "2024-08-12"),
    }
    deadline = time.time() + max(wait_sec, poll_sec)
    audio_url = ""
    task_status = ""
    last_query_json: Dict[str, Any] = {}

    while time.time() <= deadline:
        query_payload = {"TaskID": task_id}
        query_body = json.dumps(query_payload, ensure_ascii=False, separators=(",", ":"))
        if auth_mode == "bearer":
            query_headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        else:
            query_headers = _build_volc_headers(
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                host=host,
                method="POST",
                canonical_uri="/",
                query_params=query_params_sign,
                body_str=query_body,
                region=region,
                service=service,
            )
        qr = requests.post(query_url, headers=query_headers, data=query_body.encode("utf-8"), timeout=90)
        qr.raise_for_status()
        last_query_json = qr.json()
        task_status = str(_deep_get_first(last_query_json, ["TaskStatus", "Status", "State"]) or "")
        audio_url_val = _deep_get_first(last_query_json, ["AudioUrl", "SongUrl", "MusicUrl", "Url", "FileUrl"])
        if audio_url_val:
            audio_url = str(audio_url_val)
            break
        if task_status.lower() in {"failed", "error", "cancelled", "timeout"}:
            break
        time.sleep(max(1, poll_sec))

    audio_path = ""
    if download_audio and audio_url:
        audio_file = out_dir / f"{task_id}.wav"
        dl = requests.get(audio_url, timeout=120)
        dl.raise_for_status()
        audio_file.write_bytes(dl.content)
        audio_path = str(audio_file)

    return {
        "task_id": task_id,
        "task_status": task_status,
        "audio_url": audio_url,
        "audio_path": audio_path,
        "submit_url": submit_url,
        "query_url": query_url,
        "submit_response": submit_json,
        "query_response": last_query_json,
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="闭环流水线：EmoLLM -> Prompt -> SD API -> 音乐提交/查询")
    parser.add_argument("--text", required=True, help="用户输入文本")
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR))
    parser.add_argument("--prompt-csv", default=str(DEFAULT_PROMPT_CSV))
    parser.add_argument("--log-csv", default=str(DEFAULT_LOG_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ab-variant", default="", help="可选: A/B/C/D")
    parser.add_argument("--sd-api-url", default="http://127.0.0.1:7860", help="A1111 API 地址")
    parser.add_argument("--sd-width", type=int, default=768)
    parser.add_argument("--sd-height", type=int, default=768)
    parser.add_argument("--sd-steps", type=int, default=24)
    parser.add_argument("--sd-cfg-scale", type=float, default=6.0)
    parser.add_argument("--sd-seed", type=int, default=-1, help="默认 -1 每次随机出图；指定非负整数可复现图片")
    parser.add_argument("--sd-model", default="sd_xl_base_1.0.safetensors")
    parser.add_argument("--sd-lora", default="landscape-painting-sdxl_v2 (1)", help="LoRA 名称；空字符串表示不使用")
    parser.add_argument("--skip-music", action="store_true", help="仅验证本地情绪识别和出图，不调用付费音乐 API")
    parser.add_argument("--music-wait-sec", type=int, default=300)
    parser.add_argument("--music-poll-sec", type=int, default=8)
    parser.add_argument("--music-duration-sec", type=int, default=None, help="可选：覆盖音乐生成时长（接口范围30-120）")
    parser.add_argument("--no-download-audio", action="store_true", help="只查询链接，不下载音频")
    parser.add_argument("--save-case-name", default="", help="可选：按案例名归档本次输出到 deliverables")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    prompt_csv = Path(args.prompt_csv)
    log_csv = Path(args.log_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _load_env()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    operator = os.getenv("USERNAME", "unknown")
    pipe_test_id = _next_test_id(log_csv, "PIPE")
    t0 = time.perf_counter()

    status = "failed"
    error_message = ""
    emotion: Dict[str, Any] = {}
    template: Dict[str, str] = {}
    soothing_response: Dict[str, str] = {}
    payload_path = output_dir / f"{pipe_test_id}_payload.json"
    image_path = output_dir / f"{pipe_test_id}.png"
    music_bundle_path = output_dir / f"{pipe_test_id}_music.json"
    audio_path = ""
    music_task_id = ""
    case_archive_dir = ""

    try:
        emotion = infer_emotion(args.text, model_dir=model_dir)
        template = select_template(
            emotion_label=emotion["emotion_label"],
            intensity=emotion["intensity"],
            csv_path=prompt_csv,
            active_only=True,
            prefer_variant=args.ab_variant,
        )
        soothing_response = _build_soothing_response(emotion, template)
        payload = {
            "input_text": args.text,
            "emotion": emotion,
            "template": template,
            "soothing_response": soothing_response,
        }
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        _sd_txt2img(
            api_url=args.sd_api_url,
            positive=template["positive_prompt"],
            negative=template["negative_prompt"],
            width=args.sd_width,
            height=args.sd_height,
            steps=args.sd_steps,
            cfg_scale=args.sd_cfg_scale,
            out_file=image_path,
            seed=args.sd_seed,
            checkpoint=args.sd_model,
            lora=args.sd_lora,
        )

        if args.skip_music:
            music_bundle = {"task_status": "skipped"}
        else:
            duration_sec = int(emotion.get("music_profile", {}).get("duration_sec", 120))
            if args.music_duration_sec is not None:
                duration_sec = int(args.music_duration_sec)
            # GenBGMForTime 当前接口要求 [30,120] 秒
            duration_sec = max(30, min(120, duration_sec))
            music_prompt = _render_music_prompt(emotion, template, duration_sec=duration_sec)
            music_bundle = _music_submit_and_query(
                prompt=music_prompt,
                duration_sec=duration_sec,
                wait_sec=args.music_wait_sec,
                poll_sec=args.music_poll_sec,
                download_audio=(not args.no_download_audio),
                out_dir=output_dir,
            )
        music_bundle_path.write_text(json.dumps(music_bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        audio_path = str(music_bundle.get("audio_path", ""))
        music_task_id = str(music_bundle.get("task_id", ""))
        if not args.skip_music and not music_bundle.get("audio_url"):
            raise RuntimeError(f"音乐任务未返回AudioUrl，TaskID={music_task_id}")
        status = "success"
    except Exception as e:
        error_message = str(e)

    latency_ms = int((time.perf_counter() - t0) * 1000)
    output_paths = [str(payload_path)]
    if image_path.exists():
        output_paths.append(str(image_path))
    if music_bundle_path.exists():
        output_paths.append(str(music_bundle_path))
    if audio_path:
        output_paths.append(audio_path)

    note = "closed_loop_pipeline"
    if emotion and template:
        note = f"{note};emotion={emotion.get('emotion_label')}:{emotion.get('intensity')};tpl={template.get('id')};task={music_task_id}"

    _append_log(
        log_csv,
        {
            "test_id": pipe_test_id,
            "test_time": now,
            "module": "PIPE",
            "test_case": "emollm_prompt_sd_music_end2end",
            "input_summary": args.text[:100],
            "status": status,
            "latency_ms": str(latency_ms),
            "output_path": " | ".join(output_paths),
            "error_message": error_message,
            "operator": operator,
            "notes": note,
        },
    )

    if args.save_case_name:
        archive_files = [payload_path, image_path, image_path.with_suffix(".metadata.json"), music_bundle_path]
        if audio_path:
            archive_files.append(Path(audio_path))
        archived = _archive_case(
            deliverables_root=DEFAULT_DELIVERABLES_DIR,
            case_name=args.save_case_name,
            file_paths=archive_files,
            log_path=log_csv,
        )
        case_archive_dir = str(archived)

    print(
        json.dumps(
            {
                "test_id": pipe_test_id,
                "status": status,
                "latency_ms": latency_ms,
                "payload_path": str(payload_path),
                "image_path": str(image_path) if image_path.exists() else "",
                "music_info_path": str(music_bundle_path) if music_bundle_path.exists() else "",
                "audio_path": audio_path,
                "case_archive_dir": case_archive_dir,
                "error_message": error_message,
                "music_skipped": args.skip_music,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if status != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
