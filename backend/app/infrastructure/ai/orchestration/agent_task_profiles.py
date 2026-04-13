from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AgentTaskProfile:
    task_name: str
    label: str
    agent: str
    model_task_name: str
    compaction_policy: str
    memory_scope: str
    permissions: tuple[str, ...]
    required_context: tuple[str, ...] = ()
    internal_only: bool = False


def build_task_profiles(*, mode: str, attempt: int, batch_size: int) -> list[AgentTaskProfile]:
    profiles: list[AgentTaskProfile] = [
        AgentTaskProfile(
            task_name="context_shape",
            label="Building remediation context",
            agent="context_agent",
            model_task_name="repository_map",
            compaction_policy="context_shape",
            memory_scope="finding",
            permissions=("read_scan_artifacts", "read_path_evidence", "shape_context"),
            required_context=("finding", "code.window.snippet"),
            internal_only=True,
        ),
        AgentTaskProfile(
            task_name="explain_draft",
            label="Analyzing vulnerability",
            agent="explain_agent",
            model_task_name="explain",
            compaction_policy="explain",
            memory_scope="finding",
            permissions=("read_scan_artifacts", "read_code_window", "draft_security_explanation"),
            required_context=("finding", "code.window.snippet", "path"),
        ),
    ]

    if mode == "batch":
        profiles.append(
            AgentTaskProfile(
                task_name="batch_plan",
                label=f"Preparing batch remediation context for {batch_size} findings",
                agent="context_agent",
                model_task_name="fix_draft",
                compaction_policy="batch_plan",
                memory_scope="batch",
                permissions=("read_scan_artifacts", "group_validated_findings", "prioritize_batch"),
                required_context=("batch.findings",),
                internal_only=True,
            )
        )

    profiles.append(
        AgentTaskProfile(
            task_name="fix_draft",
            label="Generating fix strategies",
            agent="fix_agent",
            model_task_name="fix_draft",
            compaction_policy="fix_draft",
            memory_scope="category",
            permissions=("read_scan_artifacts", "read_code_window", "draft_patch", "rank_strategies"),
            required_context=("finding", "code.window.snippet", "path"),
        )
    )
    profiles.append(
        AgentTaskProfile(
            task_name="fix_validate",
            label="Validating fixes",
            agent="validation_agent",
            model_task_name="fix_validate",
            compaction_policy="fix_validate",
            memory_scope="category",
            permissions=("read_scan_artifacts", "read_code_window", "validate_patch"),
            required_context=("finding", "code.window.snippet"),
        )
    )

    if attempt > 1:
        profiles.append(
            AgentTaskProfile(
                task_name="fix_retry",
                label=f"Regenerating with corrective constraints (attempt {attempt})",
                agent="fix_agent",
                model_task_name="fix_draft",
                compaction_policy="fix_retry",
                memory_scope="category",
                permissions=("read_retry_memory", "exclude_weak_strategies", "regenerate_patch"),
                required_context=("retry.attempt",),
                internal_only=True,
            )
        )

    profiles.append(
        AgentTaskProfile(
            task_name="final_patch",
            label="Preparing review-ready patch",
            agent="batch_fix_agent" if mode == "batch" else "fix_agent",
            model_task_name="fix_validate",
            compaction_policy="final_patch",
            memory_scope="finding",
            permissions=("render_patch_review", "summarize_validation", "publish_plan"),
            required_context=("finding",),
            internal_only=True,
        )
    )
    return profiles
