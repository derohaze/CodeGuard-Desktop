from dataclasses import dataclass

from app.infrastructure.ai.agents.explain_agent import ExplainAgent
from app.infrastructure.ai.agents.fix_agent import FixAgent
from app.infrastructure.ai.agents.validation_agent import ValidationAgent
from app.infrastructure.ai.orchestration.agent_event_hooks import AgentEventHooks
from app.infrastructure.ai.orchestration.agent_memory_store import AgentMemoryStore
from app.infrastructure.ai.orchestration.agent_policy_engine import AgentPolicyEngine
from app.infrastructure.ai.orchestration.agent_task_profiles import AgentTaskProfile, build_task_profiles
from app.infrastructure.ai.orchestration.context_compaction import compact_agent_payload
from app.infrastructure.ai.orchestration.model_router import ModelRouter
from app.infrastructure.services.exploit_examples import enrich_explanation_examples


@dataclass(slots=True)
class RoutedTask:
    task_name: str
    label: str
    agent: str
    model: str
    permissions: tuple[str, ...] = ()
    details: list[str] | None = None


class RemediationRouter:
    def __init__(
        self,
        *,
        explain_agent: ExplainAgent,
        fix_agent: FixAgent,
        validation_agent: ValidationAgent,
        model_router: ModelRouter,
        policy_engine: AgentPolicyEngine | None = None,
        memory_store: AgentMemoryStore | None = None,
        event_hooks: AgentEventHooks | None = None,
    ) -> None:
        self.explain_agent = explain_agent
        self.fix_agent = fix_agent
        self.validation_agent = validation_agent
        self.model_router = model_router
        self.policy_engine = policy_engine or AgentPolicyEngine()
        self.memory_store = memory_store or AgentMemoryStore()
        self.event_hooks = event_hooks or AgentEventHooks()
        self._profiles: dict[str, AgentTaskProfile] = {}

    async def start_run(self, remediation_context: dict, mode: str) -> None:
        batch = remediation_context.get("batch", {}) if isinstance(remediation_context.get("batch"), dict) else {}
        tuning = remediation_context.get("retry", {}) if isinstance(remediation_context.get("retry"), dict) else {}
        attempt = int(tuning.get("attempt", 1) or 1)
        profiles = build_task_profiles(mode=mode, attempt=attempt, batch_size=len(batch.get("findings", [])))
        self._profiles = {item.task_name: item for item in profiles}
        self.event_hooks.start_run(profiles)
        self._mark_internal_steps(remediation_context, mode)

    async def explain(self, remediation_context: dict, *, mode: str = "single") -> dict:
        profile = self._profiles.get("explain_draft") or await self._task_profile("explain_draft", mode=mode, remediation_context=remediation_context)
        memory = self.memory_store.recall(profile, remediation_context, mode=mode)
        compacted_payload, compaction = compact_agent_payload("explain", remediation_context, memory=memory)
        policy_notes = self.policy_engine.check(profile, compacted_payload, mode=mode)
        self.event_hooks.before_task(profile, policy_notes=policy_notes, memory_summary=memory, compaction=compaction)
        try:
            result = await self.explain_agent.run(compacted_payload)
            result = enrich_explanation_examples(remediation_context, result)
            self.memory_store.remember(profile, remediation_context, result, mode=mode)
            self.event_hooks.after_task(profile, result=result)
            return result
        except Exception as exc:
            self.event_hooks.error_task(profile, exc)
            raise

    async def generate_fix(self, remediation_context: dict, mode: str) -> dict:
        draft_profile = self._profiles.get("fix_draft") or await self._task_profile("fix_draft", mode=mode, remediation_context=remediation_context)
        draft_memory = self.memory_store.recall(draft_profile, remediation_context, mode=mode)
        compacted_context, compaction = compact_agent_payload(
            "fix_retry" if "fix_retry" in self._profiles else "fix_draft",
            remediation_context,
            memory=draft_memory,
        )
        policy_notes = self.policy_engine.check(draft_profile, compacted_context, mode=mode)
        self.event_hooks.before_task(draft_profile, policy_notes=policy_notes, memory_summary=draft_memory, compaction=compaction)
        try:
            draft = await self.fix_agent.run(compacted_context, mode)
            self.memory_store.remember(draft_profile, remediation_context, draft, mode=mode)
            self.event_hooks.after_task(draft_profile, result=draft)
        except Exception as exc:
            self.event_hooks.error_task(draft_profile, exc)
            raise

        validation_profile = self._profiles.get("fix_validate") or await self._task_profile("fix_validate", mode=mode, remediation_context=remediation_context)
        validation_memory = self.memory_store.recall(validation_profile, remediation_context, mode=mode)
        compacted_validation, validation_compaction = compact_agent_payload(
            "fix_validate",
            remediation_context,
            draft=draft,
            memory=validation_memory,
        )
        validation_notes = self.policy_engine.check(validation_profile, compacted_validation, mode=mode)
        self.event_hooks.before_task(
            validation_profile,
            policy_notes=validation_notes,
            memory_summary=validation_memory,
            compaction=validation_compaction,
        )
        try:
            validated = await self.validation_agent.run(
                {
                    key: value
                    for key, value in compacted_validation.items()
                    if key != "draft"
                },
                draft,
                mode,
            )
            validated = _merge_validated_draft(draft, validated)
            self.memory_store.remember(validation_profile, remediation_context, validated, mode=mode)
            self.event_hooks.after_task(validation_profile, result=validated)
        except Exception as exc:
            self.event_hooks.error_task(validation_profile, exc)
            raise

        final_profile = self._profiles.get("final_patch") or await self._task_profile("final_patch", mode=mode, remediation_context=remediation_context)
        final_compaction = compact_agent_payload("final_patch", remediation_context, draft=validated)[1]
        self.event_hooks.mark_internal(
            final_profile,
            [
                f"Prepared patch review for {str((validated.get('patch') or {}).get('file', remediation_context.get('finding', {}).get('file', 'the affected file')))}.",
                f"Final patch summary uses {final_compaction.get('policy', 'final_patch')} compaction for review rendering.",
            ],
        )
        return validated

    async def build_trace(self, remediation_context: dict, mode: str) -> list[RoutedTask]:
        if not self._profiles:
            await self.start_run(remediation_context, mode)
        states = {item["task_name"]: item for item in self.event_hooks.snapshot()}
        tasks: list[RoutedTask] = []
        for profile in self._profiles.values():
            state = states.get(profile.task_name, {})
            tasks.append(
                RoutedTask(
                    task_name=profile.task_name,
                    label=profile.label,
                    agent=profile.agent,
                    model=self.model_router.route(profile.model_task_name),
                    permissions=profile.permissions,
                    details=list(state.get("details", [])),
                )
            )
        return tasks

    async def _task_profile(self, task_name: str, *, mode: str, remediation_context: dict) -> AgentTaskProfile:
        if not self._profiles:
            await self.start_run(remediation_context, mode)
        return self._profiles[task_name]

    def _mark_internal_steps(self, remediation_context: dict, mode: str) -> None:
        context_profile = self._profiles.get("context_shape")
        if context_profile is not None:
            context_payload, compaction = compact_agent_payload("context_shape", remediation_context)
            context_notes = self.policy_engine.check(context_profile, context_payload, mode=mode)
            self.event_hooks.before_task(
                context_profile,
                policy_notes=context_notes,
                memory_summary={},
                compaction=compaction,
            )
            self.event_hooks.after_task(
                context_profile,
                extra_details=[
                    f"Loaded evidence from {remediation_context.get('finding', {}).get('file', 'the affected file')}:{remediation_context.get('finding', {}).get('line', 0)}-{remediation_context.get('finding', {}).get('line_end', 0)}",
                    "Prepared agent-scoped context from the traced path and nearby code window.",
                ],
            )

        batch_profile = self._profiles.get("batch_plan")
        if batch_profile is not None:
            batch_findings = remediation_context.get("batch", {}).get("findings", [])
            self.event_hooks.mark_internal(
                batch_profile,
                [
                    f"Grouped {len(batch_findings)} validated finding(s) into the batch remediation context.",
                    "Prioritized a representative path before drafting shared remediation options.",
                ],
            )

        retry_profile = self._profiles.get("fix_retry")
        if retry_profile is not None:
            retry = remediation_context.get("retry", {}) if isinstance(remediation_context.get("retry"), dict) else {}
            excluded = retry.get("excluded_strategy_ids", [])
            self.event_hooks.mark_internal(
                retry_profile,
                [
                    f"Retry attempt {int(retry.get('attempt', 1) or 1)} activated corrective constraints.",
                    f"Excluded {len(excluded)} previously weak strategy candidate(s).",
                ],
            )


def _merge_validated_draft(draft: dict, validated: dict) -> dict:
    if not isinstance(validated, dict):
        return draft

    merged = dict(validated)
    if not merged.get("review_summary") and draft.get("review_summary"):
        merged["review_summary"] = draft["review_summary"]
    if not merged.get("recommended_strategy_id") and draft.get("recommended_strategy_id"):
        merged["recommended_strategy_id"] = draft["recommended_strategy_id"]
    if not merged.get("strategies") and draft.get("strategies"):
        merged["strategies"] = draft["strategies"]

    draft_patch = draft.get("patch") if isinstance(draft.get("patch"), dict) else {}
    validated_patch = merged.get("patch") if isinstance(merged.get("patch"), dict) else {}
    if draft_patch:
        merged_patch = dict(draft_patch)
        merged_patch.update({key: value for key, value in validated_patch.items() if value not in ("", None, [], {})})
        validation_notes = [
            *[str(item).strip() for item in draft_patch.get("validation_notes", []) if str(item).strip()],
            *[str(item).strip() for item in validated_patch.get("validation_notes", []) if str(item).strip()],
            *[str(item).strip() for item in merged.get("validation_notes", []) if str(item).strip()],
        ]
        if validation_notes:
            seen: set[str] = set()
            merged_patch["validation_notes"] = []
            for note in validation_notes:
                if note in seen:
                    continue
                seen.add(note)
                merged_patch["validation_notes"].append(note)
        merged["patch"] = merged_patch

    return merged
