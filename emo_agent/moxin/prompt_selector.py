import csv
import random
from pathlib import Path
from typing import Dict, List


DEFAULT_CSV_PATH = Path(r"D:\moxin\emotion_to_prompt.csv")


def _load_templates(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def select_template(
    emotion_label: str,
    intensity: int,
    csv_path: Path = DEFAULT_CSV_PATH,
    active_only: bool = True,
    prefer_variant: str = "",
) -> Dict[str, str]:
    rows = _load_templates(csv_path)
    if active_only:
        rows = [r for r in rows if str(r.get("ab_active", "0")).strip() == "1"]

    same_emotion = [r for r in rows if r.get("emotion_label", "").strip() == emotion_label]
    if not same_emotion:
        raise ValueError(f"模板中不存在情绪标签: {emotion_label}")

    exact = [r for r in same_emotion if int(r.get("intensity", "0")) == int(intensity)]
    candidates = exact if exact else same_emotion

    if not exact:
        candidates = sorted(
            same_emotion,
            key=lambda r: abs(int(r.get("intensity", "0")) - int(intensity)),
        )
        best_gap = abs(int(candidates[0].get("intensity", "0")) - int(intensity))
        candidates = [
            r
            for r in candidates
            if abs(int(r.get("intensity", "0")) - int(intensity)) == best_gap
        ]

    if prefer_variant:
        variant_hit = [r for r in candidates if r.get("ab_variant", "").strip().upper() == prefer_variant.upper()]
        if variant_hit:
            selected = variant_hit[0]
        else:
            selected = random.choice(candidates)
    else:
        selected = random.choice(candidates)

    selected = dict(selected)
    selected["selection_reason"] = "exact" if exact else "nearest_intensity_fallback"
    return selected


if __name__ == "__main__":
    # 便于命令行快速检查
    result = select_template("焦虑", 4)
    print(result["id"], result["emotion_label"], result["intensity"], result["selection_reason"])
