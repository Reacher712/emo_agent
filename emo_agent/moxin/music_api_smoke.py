import argparse
import csv
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote

import requests
from project_paths import LOG_CSV, OUTPUT_DIR, load_project_env

try:
    from dotenv import load_dotenv  # optional
except Exception:  # pragma: no cover
    load_dotenv = None


DEFAULT_LOG_CSV = LOG_CSV
DEFAULT_OUTPUT_DIR = OUTPUT_DIR


def _load_env():
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


def _append_log(log_csv: Path, row: Dict[str, str]) -> None:
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
    exists = log_csv.exists()
    with log_csv.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def _validate_required(name: str, value: str) -> None:
    if not value or value.startswith("__FILL_"):
        raise ValueError(f"请先填写配置: {name}")


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _canonical_query(params: Dict[str, str]) -> str:
    # 仅保留非空参数并按键排序
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
    canonical_headers = (
        f"host:{host}\n"
        f"x-content-sha256:{payload_hash}\n"
        f"x-date:{x_date}\n"
    )
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
    string_to_sign = (
        "HMAC-SHA256\n"
        f"{x_date}\n"
        f"{credential_scope}\n"
        f"{_sha256_hex(canonical_request)}"
    )

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


def main():
    parser = argparse.ArgumentParser(description="豆包音乐 API 冒烟测试（模板版）")
    parser.add_argument("--prompt", default="舒缓钢琴，治愈，2分钟", help="音乐描述")
    parser.add_argument("--duration-sec", type=int, default=120, help="期望时长（秒）")
    parser.add_argument("--style", default="calm_piano", help="风格标签")
    parser.add_argument("--emotion-label", default="焦虑", help="情绪标签（用于日志）")
    parser.add_argument("--intensity", type=int, default=3, help="情绪强度（用于日志）")
    args = parser.parse_args()

    _load_env()

    # ===== 这些配置请在 D:\\moxin\\.env 中填写 =====
    auth_mode = os.getenv("MUSIC_AUTH_MODE", "volc_aksk").strip()
    submit_url = os.getenv("MUSIC_API_SUBMIT_URL", "").strip()
    query_url = os.getenv("MUSIC_API_QUERY_URL", "").strip()
    # Bearer 模式
    api_key = os.getenv("MUSIC_API_KEY", "").strip()
    # 火山 AK/SK 签名模式
    access_key_id = os.getenv("VOLC_ACCESS_KEY_ID", "").strip()
    secret_access_key = os.getenv("VOLC_SECRET_ACCESS_KEY", "").strip()
    host = os.getenv("MUSIC_API_HOST", "open.volcengineapi.com").strip()
    action = os.getenv("MUSIC_API_ACTION", "GenBGM").strip()
    api_version = os.getenv("MUSIC_API_VERSION", "2024-08-12").strip()
    region = os.getenv("MUSIC_API_REGION", "cn-beijing").strip()
    service = os.getenv("MUSIC_API_SERVICE", "imagination").strip()
    # 可选业务字段
    tos_bucket = os.getenv("MUSIC_API_TOS_BUCKET", "").strip()
    callback_url = os.getenv("MUSIC_API_CALLBACK_URL", "").strip()
    api_model_version = os.getenv("MUSIC_API_MODEL_VERSION", "v5.0").strip()
    enable_rewrite = os.getenv("MUSIC_API_ENABLE_INPUT_REWRITE", "false").strip().lower() in ("1", "true", "yes")
    # ================================================

    payload: Dict[str, Any] = {
        "Text": args.prompt,
        "Duration": args.duration_sec,
        "TosBucket": tos_bucket,
        "CallbackURL": callback_url,
        "EnableInputRewrite": enable_rewrite,
        "Version": api_model_version,
    }

    # 非空字段清理
    payload = {k: v for k, v in payload.items() if v != ""}

    query_params = {
        "Action": action,
        "Version": api_version,
    }
    if not submit_url:
        submit_url = f"https://{host}/?{_canonical_query(query_params)}"

    request_body_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    if auth_mode == "bearer":
        _validate_required("MUSIC_API_KEY", api_key)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    else:
        _validate_required("VOLC_ACCESS_KEY_ID", access_key_id)
        _validate_required("VOLC_SECRET_ACCESS_KEY", secret_access_key)
        headers = _build_volc_headers(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            host=host,
            method="POST",
            canonical_uri="/",
            query_params=query_params,
            body_str=request_body_str,
            region=region,
            service=service,
        )

    out_dir = DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    log_csv = DEFAULT_LOG_CSV
    test_id = _next_test_id(log_csv, "MUS")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    operator = os.getenv("USERNAME", "unknown")

    t0 = time.perf_counter()
    status = "failed"
    err = ""
    response_json: Dict[str, Any] = {}
    try:
        # AK/SK 签名必须与实际发送 body 完全一致，统一发送已签名的 JSON 字符串。
        resp = requests.post(submit_url, headers=headers, data=request_body_str.encode("utf-8"), timeout=90)
        response_json = {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.json() if "application/json" in resp.headers.get("Content-Type", "") else resp.text,
            "query_url": query_url,
            "auth_mode": auth_mode,
            "submit_url": submit_url,
            "action": action,
            "version": api_version,
        }
        status = "success" if 200 <= resp.status_code < 300 else "failed"
        if status == "failed":
            err = f"http_{resp.status_code}"
    except Exception as e:
        err = str(e)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    out_path = out_dir / f"{test_id}_music_response.json"
    out_path.write_text(json.dumps(response_json, ensure_ascii=False, indent=2), encoding="utf-8")

    _append_log(
        log_csv,
        {
            "test_id": test_id,
            "test_time": now,
            "module": "MUS",
            "test_case": "music_api_smoke",
            "input_summary": f"{args.emotion_label}|{args.intensity}|{args.style}|{args.duration_sec}s",
            "status": status,
            "latency_ms": str(latency_ms),
            "output_path": str(out_path),
            "error_message": err,
            "operator": operator,
            "notes": "volc music api smoke test",
        },
    )

    print(json.dumps({"test_id": test_id, "status": status, "latency_ms": latency_ms, "output": str(out_path)}, ensure_ascii=False, indent=2))
    if status != "success":
        print("提示：若返回失败，请先按官方文档调整 payload 字段名与层级。")


if __name__ == "__main__":
    main()
