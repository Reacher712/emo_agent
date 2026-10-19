import argparse
import csv
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from urllib.parse import quote, urlparse, parse_qs

import requests

try:
    from dotenv import load_dotenv  # optional
except Exception:  # pragma: no cover
    load_dotenv = None


DEFAULT_LOG_CSV = Path(r"D:\moxin\smoke_test_log.csv")
DEFAULT_OUTPUT_DIR = Path(r"D:\moxin\outputs")


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv(Path(r"D:\moxin\.env"))


def _validate_required(name: str, value: str) -> None:
    if not value or value.startswith("__FILL_"):
        raise ValueError(f"请先填写配置: {name}")


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


def _iter_values(node: Any) -> Iterable[Any]:
    if isinstance(node, dict):
        for v in node.values():
            yield v
    elif isinstance(node, list):
        for v in node:
            yield v


def _deep_get_first(node: Any, candidate_keys: Iterable[str]) -> Optional[Any]:
    key_set = {k.lower() for k in candidate_keys}
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


def _extract_query_params_from_url(url: str) -> Dict[str, str]:
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    return {
        "Action": (q.get("Action", ["QuerySong"])[0] or "QuerySong"),
        "Version": (q.get("Version", ["2024-08-12"])[0] or "2024-08-12"),
    }


def _request_query(
    *,
    task_id: str,
    auth_mode: str,
    query_url: str,
    host: str,
    region: str,
    service: str,
    access_key_id: str,
    secret_access_key: str,
    api_key: str,
) -> Dict[str, Any]:
    body = {"TaskID": task_id}
    body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    query_params = _extract_query_params_from_url(query_url)

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
            body_str=body_str,
            region=region,
            service=service,
        )

    resp = requests.post(query_url, headers=headers, data=body_str.encode("utf-8"), timeout=90)
    parsed_body: Any
    if "application/json" in resp.headers.get("Content-Type", ""):
        parsed_body = resp.json()
    else:
        parsed_body = resp.text
    return {
        "status_code": resp.status_code,
        "headers": dict(resp.headers),
        "body": parsed_body,
        "request": {
            "query_url": query_url,
            "auth_mode": auth_mode,
            "query_payload": body,
            "query_params": query_params,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="查询豆包音乐生成任务状态并提取音频链接")
    parser.add_argument("--task-id", required=True, help="提交接口返回的 TaskID")
    parser.add_argument("--wait", action="store_true", help="轮询等待直到完成/失败/超时")
    parser.add_argument("--poll-interval-sec", type=int, default=8, help="轮询间隔秒数")
    parser.add_argument("--max-wait-sec", type=int, default=300, help="最大等待秒数")
    parser.add_argument("--download", action="store_true", help="查到音频链接后自动下载到 outputs 目录")
    args = parser.parse_args()

    _load_env()
    auth_mode = os.getenv("MUSIC_AUTH_MODE", "volc_aksk").strip()
    query_url = os.getenv("MUSIC_API_QUERY_URL", "").strip()
    host = os.getenv("MUSIC_API_HOST", "open.volcengineapi.com").strip()
    api_version = os.getenv("MUSIC_API_VERSION", "2024-08-12").strip()
    region = os.getenv("MUSIC_API_REGION", "cn-beijing").strip()
    service = os.getenv("MUSIC_API_SERVICE", "imagination").strip()
    access_key_id = os.getenv("VOLC_ACCESS_KEY_ID", "").strip()
    secret_access_key = os.getenv("VOLC_SECRET_ACCESS_KEY", "").strip()
    api_key = os.getenv("MUSIC_API_KEY", "").strip()

    if not query_url:
        query_url = f"https://{host}/?Action=QuerySong&Version={api_version}"

    t0 = time.perf_counter()
    deadline = time.time() + max(0, args.max_wait_sec)
    last_result: Dict[str, Any] = {}
    err = ""
    status = "failed"
    audio_url = ""
    task_status = ""
    local_audio_path = ""

    while True:
        try:
            current = _request_query(
                task_id=args.task_id,
                auth_mode=auth_mode,
                query_url=query_url,
                host=host,
                region=region,
                service=service,
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                api_key=api_key,
            )
            last_result = current
            http_ok = 200 <= int(current.get("status_code", 0)) < 300
            body = current.get("body", {})
            audio_url_val = _deep_get_first(body, ["AudioUrl", "SongUrl", "MusicUrl", "Url", "FileUrl"])
            task_status_val = _deep_get_first(body, ["TaskStatus", "Status", "State"])
            code_val = _deep_get_first(body, ["Code"])
            message_val = _deep_get_first(body, ["Message"])

            if audio_url_val:
                audio_url = str(audio_url_val)
            if task_status_val is not None:
                task_status = str(task_status_val)

            done_states = {"success", "succeeded", "done", "finish", "finished", "complete", "completed"}
            fail_states = {"failed", "error", "canceled", "cancelled", "timeout"}
            normalized_state = task_status.strip().lower()

            if http_ok and audio_url:
                status = "success"
                break
            if normalized_state in fail_states:
                status = "failed"
                break
            if not args.wait:
                status = "success" if http_ok else "failed"
                if not http_ok:
                    err = f"http_{current.get('status_code')}"
                elif str(code_val) not in ("0", "", "None"):
                    err = f"api_code_{code_val}:{message_val}"
                break
            if normalized_state in done_states and not audio_url:
                status = "failed"
                err = "done_but_no_audio_url"
                break
            if time.time() >= deadline:
                status = "failed"
                err = "query_timeout"
                break
            time.sleep(max(1, args.poll_interval_sec))
        except Exception as e:
            last_result = {"exception": str(e)}
            status = "failed"
            err = str(e)
            break

    latency_ms = int((time.perf_counter() - t0) * 1000)
    out_dir = DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    if status == "success" and audio_url and args.download:
        audio_file = out_dir / f"{args.task_id}.wav"
        try:
            dl_resp = requests.get(audio_url, timeout=120)
            dl_resp.raise_for_status()
            audio_file.write_bytes(dl_resp.content)
            local_audio_path = str(audio_file)
        except Exception as e:
            err = f"{err};download_failed:{e}" if err else f"download_failed:{e}"

    out_path = out_dir / f"{args.task_id}_query_response.json"
    out_path.write_text(json.dumps(last_result, ensure_ascii=False, indent=2), encoding="utf-8")

    log_csv = DEFAULT_LOG_CSV
    test_id = _next_test_id(log_csv, "MUS")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    operator = os.getenv("USERNAME", "unknown")
    _append_log(
        log_csv,
        {
            "test_id": test_id,
            "test_time": now,
            "module": "MUS",
            "test_case": "music_api_query",
            "input_summary": f"task_id={args.task_id}",
            "status": status,
            "latency_ms": str(latency_ms),
            "output_path": str(out_path),
            "error_message": err,
            "operator": operator,
            "notes": f"task_status={task_status}; audio_url={'yes' if audio_url else 'no'}; local_audio={'yes' if local_audio_path else 'no'}",
        },
    )

    print(
        json.dumps(
            {
                "test_id": test_id,
                "status": status,
                "latency_ms": latency_ms,
                "task_id": args.task_id,
                "task_status": task_status,
                "audio_url": audio_url,
                "local_audio_path": local_audio_path,
                "output": str(out_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
