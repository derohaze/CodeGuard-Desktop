from __future__ import annotations

from textwrap import shorten

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalAIServiceError
from app.domain.services.ai_client import SecurityAnalysisAIClient
from app.infrastructure.ai.client_utils import (
    compact_findings,
    extract_json,
    extract_review_payload,
    json_for_prompt,
    json_for_task_prompt,
    normalize_fix_strategy,
    normalize_patch_candidate,
    normalize_priority_path,
)
from app.infrastructure.ai.groq_key_pool import GroqKeyPool
from app.infrastructure.ai.orchestration.model_router import ModelRouter
from app.infrastructure.ai.prompt_loader import load_prompt_pack


class GroqSecurityClient(SecurityAnalysisAIClient):
    def __init__(self) -> None:
        settings = get_settings()
        self.provider_name = "groq"
        api_keys = list(settings.groq_api_keys or [])
        if not api_keys and settings.groq_api_key:
            api_keys = [settings.groq_api_key]
        self.base_url = settings.groq_base_url.rstrip("/")
        self.small_model = settings.groq_small_model or "openai/gpt-oss-20b"
        self.large_model = settings.groq_large_model or settings.groq_model or "openai/gpt-oss-120b"
        self.overflow_model = settings.groq_overflow_model or "groq/compound-mini"
        self.scout_model = settings.groq_secondary_fallback_model
        self.model_router = ModelRouter(
            small_model=self.small_model,
            large_model=self.large_model,
            overflow_model=self.overflow_model,
            scout_model=self.scout_model,
        )
        self.key_pool = GroqKeyPool(
            api_keys,
            cooldown_seconds=settings.groq_key_cooldown_seconds,
            failure_threshold=settings.groq_key_failure_threshold,
            quarantine_seconds=settings.groq_key_quarantine_seconds,
        )
        self._runtime_events: list[str] = []
        self._runtime_metrics = {
            "model_calls": {},
            "rate_limit_headers_seen": 0,
            "key_pool": self.key_pool.snapshot(),
        }

    def reset_runtime_state(self) -> None:
        self._runtime_events = []
        self._runtime_metrics = {
            "model_calls": {},
            "rate_limit_headers_seen": 0,
            "key_pool": self.key_pool.snapshot(),
        }

    def drain_runtime_events(self) -> list[str]:
        events = list(self._runtime_events)
        self._runtime_events.clear()
        return events

    def snapshot_runtime_metrics(self, *, reset: bool = False) -> dict:
        snapshot = {
            **self._runtime_metrics,
            "key_pool": self.key_pool.snapshot(),
        }
        if reset:
            self.reset_runtime_state()
        return snapshot

    async def map_repository(
        self,
        project_name: str,
        source_path: str,
        repository_profile: dict,
        repository_artifacts: dict,
        preset: str,
    ) -> dict:
        completion = await self._create_completion(
            task_name="repository_map",
            max_completion_tokens=1024,
            messages=[
                {"role": "system", "content": load_prompt_pack("repository_mapper.md")},
                {
                    "role": "user",
                    "content": (
                        f"Project: {project_name}\n"
                        f"Source: {source_path}\n"
                        f"Preset: {preset}\n"
                        f"Repository profile JSON: {json_for_task_prompt('repository_map', 'repository_profile', repository_profile, max_chars=1800)}\n"
                        f"Repository artifacts JSON: {json_for_task_prompt('repository_map', 'repository_artifacts', repository_artifacts, max_chars=2800)}"
                    ),
                },
            ],
        )
        content = _completion_message_text(completion)
        parsed = extract_json(content)
        if not parsed:
            raise ExternalAIServiceError(
                "Groq returned a completion without JSON content for repository mapping.",
                provider="groq",
                retryable=True,
                failure_kind="output_format",
            )
        return {
            "review_note": shorten(str(parsed.get("review_note", "")), width=180, placeholder="..."),
            "repository_summary": shorten(str(parsed.get("repository_summary", "")), width=260, placeholder="..."),
            "coverage_note": shorten(str(parsed.get("coverage_note", "")), width=220, placeholder="..."),
            "trust_boundaries": [str(item) for item in parsed.get("trust_boundaries", []) if str(item).strip()][:10],
            "priority_paths": [normalize_priority_path(item) for item in parsed.get("priority_paths", []) if isinstance(item, dict)],
        }

    async def review_paths(
        self,
        project_name: str,
        source_path: str,
        repository_profile: dict,
        repository_map: dict,
        work_items: list[dict[str, str]],
        batch_index: int,
        total_batches: int,
        preset: str,
    ) -> dict:
        if not work_items:
            return {"review_note": "No prioritized work items reached the path reviewer.", "repository_summary": "", "findings": []}

        completion = await self._create_completion(
            task_name="path_review",
            max_completion_tokens=1536,
            messages=[
                {"role": "system", "content": load_prompt_pack("path_reviewer.md")},
                {
                    "role": "user",
                    "content": (
                        f"Project: {project_name}\n"
                        f"Source: {source_path}\n"
                        f"Preset: {preset}\n"
                        f"Batch: {batch_index}/{total_batches}\n"
                        f"Repository profile JSON: {json_for_task_prompt('path_review', 'repository_profile', repository_profile, max_chars=1200)}\n"
                        f"Repository map JSON: {json_for_task_prompt('path_review', 'repository_map', repository_map, max_chars=1800)}\n"
                        f"Prioritized work items JSON: {json_for_task_prompt('path_review', 'work_items', work_items, max_chars=2600)}"
                    ),
                },
            ],
        )
        content = _completion_message_text(completion)
        if not extract_json(content):
            raise ExternalAIServiceError(
                "Groq returned a completion without JSON content for path review.",
                provider="groq",
                retryable=True,
                failure_kind="output_format",
            )
        return extract_review_payload(content)

    async def validate_findings(
        self,
        project_name: str,
        source_path: str,
        repository_profile: dict,
        repository_map: dict,
        findings: list[dict],
        preset: str,
    ) -> dict:
        if not findings:
            return {
                "review_note": "The validator did not receive any candidate findings.",
                "safe_summary": "No confirmed high-confidence issue was found in the reviewed scope.",
                "findings": [],
            }

        completion = await self._create_completion(
            task_name="finding_validate",
            max_completion_tokens=1536,
            messages=[
                {"role": "system", "content": load_prompt_pack("finding_validator.md")},
                {
                    "role": "user",
                    "content": (
                        f"Project: {project_name}\n"
                        f"Source: {source_path}\n"
                        f"Preset: {preset}\n"
                        f"Repository profile JSON: {json_for_task_prompt('finding_validate', 'repository_profile', repository_profile, max_chars=1200)}\n"
                        f"Repository map JSON: {json_for_task_prompt('finding_validate', 'repository_map', repository_map, max_chars=1800)}\n"
                        f"Potential findings JSON: {json_for_task_prompt('finding_validate', 'findings', compact_findings(findings, limit=18), max_chars=2200)}"
                    ),
                },
            ],
        )
        content = _completion_message_text(completion)
        if not extract_json(content):
            raise ExternalAIServiceError(
                "Groq returned a completion without JSON content for finding validation.",
                provider="groq",
                retryable=True,
                failure_kind="output_format",
            )
        parsed = extract_review_payload(content)
        return {
            "review_note": shorten(str(parsed.get("review_note", "")), width=180, placeholder="..."),
            "safe_summary": shorten(str(parsed.get("safe_summary", "")), width=220, placeholder="..."),
            "findings": parsed.get("findings", []),
        }

    async def summarize_verdict(
        self,
        project_name: str,
        source_path: str,
        repository_profile: dict,
        repository_map: dict,
        findings: list[dict],
        security_score: int | None,
        preset: str,
    ) -> dict:
        completion = await self._create_completion(
            task_name="verdict",
            max_completion_tokens=768,
            messages=[
                {"role": "system", "content": load_prompt_pack("verdict_analyst.md")},
                {
                    "role": "user",
                    "content": (
                        f"Project: {project_name}\n"
                        f"Source: {source_path}\n"
                        f"Preset: {preset}\n"
                        f"Security score: {security_score}\n"
                        f"Repository profile JSON: {json_for_task_prompt('verdict', 'repository_profile', repository_profile, max_chars=1000)}\n"
                        f"Repository map JSON: {json_for_task_prompt('verdict', 'repository_map', repository_map, max_chars=1600)}\n"
                        f"Confirmed findings JSON: {json_for_task_prompt('verdict', 'findings', compact_findings(findings, limit=16), max_chars=1800)}"
                    ),
                },
            ],
        )
        content = _completion_message_text(completion)
        parsed = extract_json(content)
        if not parsed:
            raise ExternalAIServiceError(
                "Groq returned a completion without JSON content for verdict summary.",
                provider="groq",
                retryable=True,
                failure_kind="output_format",
            )
        return {
            "review_note": shorten(str(parsed.get("review_note", "")), width=180, placeholder="..."),
            "repository_summary": shorten(str(parsed.get("repository_summary", "")), width=260, placeholder="..."),
            "coverage_summary": shorten(str(parsed.get("coverage_summary", "")), width=220, placeholder="..."),
        }

    async def explain_finding(self, remediation_context: dict) -> dict:
        completion = await self._create_completion(
            task_name="explain",
            max_completion_tokens=1024,
            messages=[
                {"role": "system", "content": load_prompt_pack("explain_prompt.md")},
                {"role": "user", "content": f"Remediation context JSON: {json_for_task_prompt('explain', 'remediation_context', remediation_context, max_chars=2600)}"},
            ],
        )
        content = _completion_message_text(completion)
        parsed = extract_json(content)
        if not parsed:
            raise ExternalAIServiceError(
                "Groq returned a completion without JSON content for the explanation request.",
                provider="groq",
                retryable=True,
                failure_kind="output_format",
            )
        return {
            "summary": shorten(str(parsed.get("summary", "")), width=240, placeholder="..."),
            "exploit_scenario": shorten(str(parsed.get("exploit_scenario", "")), width=560, placeholder="..."),
            "request_example": str(parsed.get("request_example", "")),
            "payload_example": str(parsed.get("payload_example", "")),
            "attack_steps": [str(item) for item in parsed.get("attack_steps", []) if str(item).strip()][:6],
            "entry_point": shorten(str(parsed.get("entry_point", "")), width=180, placeholder="..."),
            "execution_path": shorten(str(parsed.get("execution_path", "")), width=240, placeholder="..."),
            "sink": shorten(str(parsed.get("sink", "")), width=140, placeholder="..."),
            "impact": shorten(str(parsed.get("impact", "")), width=220, placeholder="..."),
        }

    async def draft_fix_strategies(self, remediation_context: dict, mode: str) -> dict:
        completion = await self._create_completion(
            task_name="fix_draft",
            max_completion_tokens=1536,
            messages=[
                {"role": "system", "content": load_prompt_pack("fix_prompt.md")},
                {"role": "user", "content": f"Mode: {mode}\nRemediation context JSON: {json_for_task_prompt('fix_draft', 'remediation_context', remediation_context, max_chars=2800)}"},
            ],
        )
        content = _completion_message_text(completion)
        parsed = extract_json(content)
        if not parsed:
            raise ExternalAIServiceError(
                "Groq returned a completion without JSON content for remediation strategies.",
                provider="groq",
                retryable=True,
                failure_kind="output_format",
            )
        return {
            "review_summary": shorten(str(parsed.get("review_summary", "")), width=280, placeholder="..."),
            "recommended_strategy_id": str(parsed.get("recommended_strategy_id", "")).strip() or None,
            "strategies": [normalize_fix_strategy(item) for item in parsed.get("strategies", []) if isinstance(item, dict)],
            "patch": normalize_patch_candidate(parsed.get("patch", {})),
        }

    async def validate_remediation(self, remediation_context: dict, remediation_draft: dict, mode: str) -> dict:
        completion = await self._create_completion(
            task_name="fix_validate",
            max_completion_tokens=1536,
            messages=[
                {"role": "system", "content": load_prompt_pack("fix_validator_prompt.md")},
                {
                    "role": "user",
                    "content": (
                        f"Mode: {mode}\n"
                        f"Remediation context JSON: {json_for_task_prompt('fix_validate', 'remediation_context', remediation_context, max_chars=2200)}\n"
                        f"Draft remediation JSON: {json_for_task_prompt('fix_validate', 'remediation_draft', remediation_draft, max_chars=2200)}"
                    ),
                },
            ],
        )
        content = _completion_message_text(completion)
        parsed = extract_json(content)
        if not parsed:
            raise ExternalAIServiceError(
                "Groq returned a completion without JSON content for remediation validation.",
                provider="groq",
                retryable=True,
                failure_kind="output_format",
            )
        strategies = [normalize_fix_strategy(item) for item in parsed.get("strategies", remediation_draft.get("strategies", [])) if isinstance(item, dict)]
        patch = normalize_patch_candidate(parsed.get("patch", remediation_draft.get("patch", {})))
        validation_notes = [str(item) for item in parsed.get("validation_notes", []) if str(item).strip()]
        if validation_notes:
            patch["validation_notes"] = validation_notes
        return {
            "review_summary": shorten(str(parsed.get("review_summary", remediation_draft.get("review_summary", ""))), width=280, placeholder="..."),
            "recommended_strategy_id": str(parsed.get("recommended_strategy_id", remediation_draft.get("recommended_strategy_id") or "")).strip() or None,
            "strategies": strategies,
            "patch": patch,
        }

    async def _create_completion(self, *, task_name: str, max_completion_tokens: int, messages: list[dict]) -> dict:
        model_candidates = self.model_router.route_candidates(task_name)
        last_error: ExternalAIServiceError | None = None

        for model in model_candidates:
            key_info = await self.key_pool.acquire_key()
            api_key = key_info.get("api_key", "")
            label = key_info.get("label", "groq-key")
            retry_after = float(key_info.get("retry_after_seconds", 0.0) or 0.0)
            if not api_key:
                last_error = ExternalAIServiceError(
                    f"All Groq keys are temporarily cooling down. Retry after about {retry_after:.1f}s.",
                    provider="groq",
                    retryable=True,
                    failure_kind="cooldown",
                )
                continue

            self._runtime_metrics["model_calls"][model] = self._runtime_metrics["model_calls"].get(model, 0) + 1

            try:
                completion = await self._post_completion(api_key=api_key, model=model, max_completion_tokens=max_completion_tokens, messages=messages)
                headers = completion.get("_headers", {})
                if headers:
                    self._runtime_metrics["rate_limit_headers_seen"] += 1
                await self.key_pool.mark_success(label, headers=headers)
                return completion
            except ExternalAIServiceError as exc:
                last_error = exc
                if exc.failure_kind == "rate_limit":
                    cooldown = await self.key_pool.mark_rate_limited(label)
                else:
                    cooldown = await self.key_pool.mark_failure(label, severe=exc.failure_kind in {"gateway", "billing"})
                continue

        if last_error is not None:
            raise last_error
        raise ExternalAIServiceError("Groq could not produce a completion.", provider="groq", retryable=True, failure_kind="runtime")

    async def _post_completion(self, *, api_key: str, model: str, max_completion_tokens: int, messages: list[dict]) -> dict:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.02,
            "top_p": 1,
            "max_completion_tokens": max_completion_tokens,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        url = f"{self.base_url}/openai/v1/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
        except httpx.TimeoutException as exc:
            raise ExternalAIServiceError(
                "Groq timed out while processing the request. Retry shortly or fail over to another provider.",
                provider="groq",
                retryable=True,
                failure_kind="timeout",
            ) from exc
        except httpx.ConnectError as exc:
            raise ExternalAIServiceError(
                "CodeGuard could not reach Groq. Check network access and retry the scan.",
                provider="groq",
                retryable=True,
                failure_kind="connection",
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise _map_groq_http_error(exc.response) from exc
        except httpx.HTTPError as exc:
            raise ExternalAIServiceError(
                "Groq could not complete the request because of an upstream runtime failure.",
                provider="groq",
                retryable=True,
                failure_kind="runtime",
            ) from exc

        body["_headers"] = dict(response.headers)
        return body


def _completion_message_text(completion: dict) -> str:
    choices = completion.get("choices", [])
    if not choices:
        return "{}"
    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning
    return "{}"


def _extract_provider_message(body: dict | None) -> str:
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        detail = body.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    return "Unknown provider error."


def _map_groq_http_error(response: httpx.Response) -> ExternalAIServiceError:
    try:
        body = response.json()
    except ValueError:
        body = None
    message = _extract_provider_message(body)
    normalized = message.lower()
    status_code = response.status_code
    if "organization_delinquent" in normalized or "overdue payment" in normalized or "restricted because of overdue payment" in normalized:
        return ExternalAIServiceError(
            "The configured Groq account is currently unavailable because billing is restricted. Update the Groq billing method and contact support, then retry the scan.",
            provider="groq",
            retryable=False,
            status_code=status_code,
            failure_kind="billing",
        )
    if status_code == 429:
        return ExternalAIServiceError(
            "Groq rate limits were reached while processing the request. Retry in a moment.",
            provider="groq",
            retryable=True,
            status_code=status_code,
            failure_kind="rate_limit",
        )
    if status_code == 413 or "request too large" in normalized or "tokens per minute" in normalized:
        return ExternalAIServiceError(
            "The current Groq account tier cannot fit this request size. CodeGuard needs either smaller prompt budgets or a provider/account with a higher TPM limit.",
            provider="groq",
            retryable=True,
            status_code=status_code,
            failure_kind="payload_too_large",
        )
    if status_code in {502, 503, 504}:
        return ExternalAIServiceError(
            f"Groq returned an upstream gateway error ({status_code}). Retry the request.",
            provider="groq",
            retryable=True,
            status_code=status_code,
            failure_kind="gateway",
        )
    if status_code >= 500:
        return ExternalAIServiceError(
            f"Groq returned an unexpected upstream error ({status_code}). Retry the request.",
            provider="groq",
            retryable=True,
            status_code=status_code,
            failure_kind="upstream",
        )
    return ExternalAIServiceError(
        f"Groq rejected the remediation or scan request: {message}",
        provider="groq",
        retryable=False,
        status_code=status_code,
        failure_kind="request_rejected",
    )
