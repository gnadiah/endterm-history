"""Quiz history persistence."""
from __future__ import annotations

import json
import os
from datetime import datetime


def _history_path() -> str:
    from .data import _project_root
    return os.path.join(_project_root(), "history.json")


def load_history() -> list[dict]:
    path = _history_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_record(
    mode: str,
    section: str | None,
    correct: int,
    total: int,
    wrong_ids: list[str],
    duration_sec: float,
) -> None:
    history = load_history()
    history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "section": section,
            "correct": correct,
            "total": total,
            "wrong_ids": wrong_ids,
            "duration_sec": round(duration_sec, 1),
        }
    )
    with open(_history_path(), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
