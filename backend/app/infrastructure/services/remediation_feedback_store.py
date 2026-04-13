from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RemediationFeedbackStore:
    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or (Path(__file__).resolve().parents[3] / "evals" / "artifacts" / "remediation_failures.jsonl")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def record_failure(self, item: dict[str, Any]) -> None:
        normalized = {key: value for key, value in item.items() if value is not None}
        with self.storage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")

    def get_recent_failures(self, category: str, limit: int = 5) -> list[dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        results: list[dict[str, Any]] = []
        with self.storage_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(item.get("category", "")).strip().lower() != category.strip().lower():
                    continue
                results.append(item)
        return results[-limit:]
