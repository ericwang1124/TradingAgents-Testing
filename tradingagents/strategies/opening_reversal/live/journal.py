"""Per-day journal files: journal/opening_reversal/YYYY-MM-DD/{briefing,decision,execution,evaluation}.json"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from .settings import JOURNAL_DIR


def day_dir(day: date, root: Path = JOURNAL_DIR) -> Path:
    path = root / day.isoformat()
    path.mkdir(parents=True, exist_ok=True)
    return path


def write(day: date, name: str, payload: Dict[str, Any], root: Path = JOURNAL_DIR) -> Path:
    path = day_dir(day, root) / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False))
    return path


def read(day: date, name: str, root: Path = JOURNAL_DIR) -> Optional[Dict[str, Any]]:
    path = root / day.isoformat() / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def journal_days(root: Path = JOURNAL_DIR) -> List[date]:
    if not root.exists():
        return []
    out = []
    for p in root.iterdir():
        try:
            out.append(date.fromisoformat(p.name))
        except ValueError:
            continue
    return sorted(out)
