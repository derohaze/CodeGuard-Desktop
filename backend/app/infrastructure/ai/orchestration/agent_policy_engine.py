from __future__ import annotations

from app.infrastructure.ai.orchestration.agent_task_profiles import AgentTaskProfile


class AgentPolicyEngine:
    def check(self, profile: AgentTaskProfile, payload: dict, *, mode: str) -> list[str]:
        missing = [path for path in profile.required_context if _is_missing(_resolve_path(payload, path))]
        if missing:
            raise ValueError(
                f"{profile.agent} cannot run because required remediation context is missing: {', '.join(missing)}."
            )

        notes = [f"Allowed actions: {', '.join(profile.permissions)}"]
        if mode == "batch" and profile.memory_scope == "batch":
            batch_findings = _resolve_path(payload, "batch.findings") or []
            notes.append(f"Batch scope includes {len(batch_findings)} finding(s).")
        if profile.task_name == "fix_validate":
            draft = payload.get("draft", {}) if isinstance(payload.get("draft"), dict) else {}
            has_draft_shape = bool(draft.get("strategies") or (draft.get("patch") or {}).get("diff"))
            notes.append(
                "Validation will inspect a concrete remediation draft."
                if has_draft_shape
                else "Validation is running on a sparse draft and may request regeneration."
            )
        return notes


def _resolve_path(payload: dict, dotted_path: str):
    current = payload
    for key in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _is_missing(value) -> bool:
    if value in (None, "", []):
        return True
    if isinstance(value, dict) and not value:
        return True
    return False
