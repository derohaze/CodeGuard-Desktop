from __future__ import annotations

from copy import deepcopy

from app.infrastructure.ai.orchestration.agent_task_profiles import AgentTaskProfile


class AgentEventHooks:
    def __init__(self) -> None:
        self._steps: dict[str, dict] = {}
        self._order: list[str] = []

    def start_run(self, profiles: list[AgentTaskProfile]) -> None:
        self._order = [item.task_name for item in profiles]
        self._steps = {
            item.task_name: {
                "task_name": item.task_name,
                "label": item.label,
                "agent": item.agent,
                "status": "pending",
                "details": [],
                "permissions": list(item.permissions),
            }
            for item in profiles
        }

    def before_task(self, profile: AgentTaskProfile, *, policy_notes: list[str], memory_summary: dict, compaction: dict) -> None:
        step = self._steps.setdefault(profile.task_name, self._fallback_step(profile))
        step["status"] = "running"
        step["details"] = _dedupe(
            [
                *step["details"],
                *policy_notes,
                _memory_note(memory_summary),
                _compaction_note(compaction),
            ]
        )

    def after_task(self, profile: AgentTaskProfile, *, result: dict | None = None, extra_details: list[str] | None = None) -> None:
        step = self._steps.setdefault(profile.task_name, self._fallback_step(profile))
        step["status"] = "done"
        details = list(step["details"])
        if result:
            details.extend(_result_details(profile.task_name, result))
        if extra_details:
            details.extend(extra_details)
        step["details"] = _dedupe(details)

    def mark_internal(self, profile: AgentTaskProfile, details: list[str]) -> None:
        step = self._steps.setdefault(profile.task_name, self._fallback_step(profile))
        step["status"] = "done"
        step["details"] = _dedupe([*step["details"], *details])

    def error_task(self, profile: AgentTaskProfile, error: Exception) -> None:
        step = self._steps.setdefault(profile.task_name, self._fallback_step(profile))
        step["status"] = "done"
        step["details"] = _dedupe([*step["details"], f"Task error: {str(error).strip()}"])

    def snapshot(self) -> list[dict]:
        return [deepcopy(self._steps[task_name]) for task_name in self._order if task_name in self._steps]

    @staticmethod
    def _fallback_step(profile: AgentTaskProfile) -> dict:
        return {
            "task_name": profile.task_name,
            "label": profile.label,
            "agent": profile.agent,
            "status": "pending",
            "details": [],
            "permissions": list(profile.permissions),
        }


def _memory_note(memory_summary: dict) -> str:
    if not memory_summary:
        return "No prior agent context was reused for this step."
    if memory_summary.get("hit"):
        return f"Reused {memory_summary.get('entry_count', 1)} prior context item(s) for this step."
    return "No prior agent context was reused for this step."


def _compaction_note(compaction: dict) -> str:
    if not compaction:
        return "Prepared a minimal context package for this step."
    return "Prepared a minimal context package focused on the traced file, path, and evidence."


def _result_details(task_name: str, result: dict) -> list[str]:
    if task_name == "explain_draft":
        return [
            f"Explained entry point: {str(result.get('entry_point', '')).strip() or 'unknown'}",
            f"Explained sink: {str(result.get('sink', '')).strip() or 'unknown'}",
        ]
    if task_name in {"fix_draft", "fix_retry"}:
        strategies = [item for item in result.get("strategies", []) if isinstance(item, dict)]
        labels = [str(item.get("label", "strategy")).strip() for item in strategies[:3] if str(item.get("label", "")).strip()]
        return [
            f"Prepared {len(strategies)} remediation strateg{'y' if len(strategies) == 1 else 'ies'}.",
            *(f"Compared {label}" for label in labels),
        ]
    if task_name == "fix_validate":
        patch = result.get("patch", {}) if isinstance(result.get("patch"), dict) else {}
        notes = [str(item).strip() for item in patch.get("validation_notes", []) if str(item).strip()][:3]
        if not notes:
            notes = ["Validation completed without additional notes."]
        return notes
    return []


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
