"""疗效评估记录持久化（本地 JSON，匿名）。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_STORE = Path(__file__).resolve().parent / "outputs" / "efficacy_records.json"


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def load_records(path: Path = DEFAULT_STORE) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        rec = data.get("records")
        return list(rec) if isinstance(rec, list) else []
    except Exception:
        return []


def append_record(record: Dict[str, Any], path: Path = DEFAULT_STORE) -> None:
    _ensure_parent(path)
    records = load_records(path)
    record = {**record, "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    records.append(record)
    path.write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
