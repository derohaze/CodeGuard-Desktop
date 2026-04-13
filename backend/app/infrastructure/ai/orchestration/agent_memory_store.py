from __future__ import annotations

from collections import deque
from copy import deepcopy

from app.infrastructure.ai.orchestration.agent_task_profiles import AgentTaskProfile


class AgentMemoryStore:
    def __init__(self, max_entries_per_scope: int = 4) -> None:
        self.max_entries_per_scope = max_entries_per_scope
        self._memory: dict[str, deque[dict]] = {}

    def recall(self, profile: AgentTaskProfile, payload: dict, *, mode: str) -> dict:
        scope_key = self._scope_key(profile, payload, mode=mode)
        entries = list(self._memory.get(scope_key, deque()))
        latest = deepcopy(entries[-1]) if entries else {}
        return {
            "scope_key": scope_key,
            "hit": bool(entries),
            "entry_count": len(entries),
            "latest": latest,
        }

    def remember(self, profile: AgentTaskProfile, payload: dict, result: dict, *, mode: str) -> None:
        scope_key = self._scope_key(profile, payload, mode=mode)
        if scope_key not in self._memory:
            self._memory[scope_key] = deque(maxlen=self.max_entries_per_scope)
        self._memory[scope_key].append(_summarize_result(result))

    def _scope_key(self, profile: AgentTaskProfile, payload: dict, *, mode: str) -> str:
        finding = payload.get("finding", {}) if isinstance(payload.get("finding"), dict) else {}
        category = str(finding.get("category", "unknown")).strip().lower() or "unknown"
        finding_id = str(finding.get("id", "unknown")).strip() or "unknown"
        file_path = str(finding.get("file", "unknown")).strip() or "unknown"
        if profile.memory_scope == "finding":
            return f"{profile.agent}:{mode}:finding:{finding_id}"
        if profile.memory_scope == "batch":
            batch = payload.get("batch", {}) if isinstance(payload.get("batch"), dict) else {}
            finding_ids = [
                str(item.get("id", "")).strip()
                for item in batch.get("findings", [])
                if isinstance(item, dict) and str(item.get("id", "")).strip()
            ]
            joined = ",".join(sorted(finding_ids)) or file_path
            return f"{profile.agent}:{mode}:batch:{joined}"
        return f"{profile.agent}:{mode}:category:{category}:{file_path}"


def _summarize_result(result: dict) -> dict:
    if not isinstance(result, dict):
        return {"summary": "Agent returned a non-dict payload."}
    strategies = result.get("strategies", [])
    patch = result.get("patch", {}) if isinstance(result.get("patch"), dict) else {}
    validation_notes = [str(item) for item in patch.get("validation_notes", []) if str(item).strip()][:3]
    return {
        "keys": list(result.keys())[:8],
        "strategy_ids": [
            str(item.get("id", "")).strip()
            for item in strategies[:4]
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        ],
        "patch_file": str(patch.get("file", "")).strip(),
        "validation_notes": validation_notes,
        "summary": str(result.get("summary", result.get("review_summary", ""))).strip()[:240],
    }
