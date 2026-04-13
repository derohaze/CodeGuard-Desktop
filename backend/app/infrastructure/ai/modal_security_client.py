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
    json_for_task_prompt,
    normalize_fix_strategy,
    normalize_patch_candidate,
    normalize_priority_path,
)
from app.infrastructure.ai.orchestration.model_router import ModelRouter
from app.infrastructure.ai.prompt_loader import load_prompt_pack


class ModalSecurityClient(SecurityAnalysisAIClient):
    def __init__(self) -> None:
        settings = get_settings()
        self.provider_name = "modal"
        self.api_key = settings.modal_api_key
        self.base_url = settings.modal_base_url.rstrip("/")
        self.small_model = settings.modal_small_model or settings.modal_model
        self.large_model = settings.modal_large_model or settings.modal_model
        self.model_router = ModelRouter(small_model=self.small_model, large_model=self.large_model)

    async def map_repository(self, project_name: str, source_path: str, repository_profile: dict, repository_artifacts: dict, preset: str) -> dict:
        parsed = await self._chat_json(
            task_name="repository_map",
            max_tokens=1024,
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
        return {
            "review_note": shorten(str(parsed.get("review_note", "")), width=180, placeholder="..."),
            "repository_summary": shorten(str(parsed.get("repository_summary", "")), width=260, placeholder="..."),
            "coverage_note": shorten(str(parsed.get("coverage_note", "")), width=220, placeholder="..."),
            "trust_boundaries": [str(item) for item in parsed.get("trust_boundaries", []) if str(item).strip()][:10],
            "priority_paths": [normalize_priority_path(item) for item in parsed.get("priority_paths", []) if isinstance(item, dict)],
        }

    async def review_paths(self, project_name: str, source_path: str, repository_profile: dict, repository_map: dict, work_items: list[dict[str, str]], batch_index: int, total_batches: int, preset: str) -> dict:
        if not work_items:
            return {"review_note": "No prioritized work items reached the path reviewer.", "repository_summary": "", "findings": []}
        content = await self._chat_text(
            task_name="path_review",
            max_tokens=1536,
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
        if not extract_json(content):
            raise ExternalAIServiceError(
                "Modal returned a completion without JSON content for path review.",
                provider="modal",
                retryable=True,
                failure_kind="output_format",
            )
        return extract_review_payload(content)

    async def validate_findings(self, project_name: str, source_path: str, repository_profile: dict, repository_map: dict, findings: list[dict], preset: str) -> dict:
        if not findings:
            return {"review_note": "The validator did not receive any candidate findings.", "safe_summary": "No confirmed high-confidence issue was found in the reviewed scope.", "findings": []}
        content = await self._chat_text(
            task_name="finding_validate",
            max_tokens=1536,
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
        if not extract_json(content):
            raise ExternalAIServiceError(
                "Modal returned a completion without JSON content for finding validation.",
                provider="modal",
                retryable=True,
                failure_kind="output_format",
            )
        parsed = extract_review_payload(content)
        return {
            "review_note": parsed["review_note"],
            "safe_summary": shorten(str(parsed.get("safe_summary", "")), width=220, placeholder="..."),
            "findings": parsed["findings"],
        }

    async def summarize_verdict(self, project_name: str, source_path: str, repository_profile: dict, repository_map: dict, findings: list[dict], security_score: int | None, preset: str) -> dict:
        parsed = await self._chat_json(
            task_name="verdict",
            max_tokens=768,
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
        return {
            "review_note": shorten(str(parsed.get("review_note", "")), width=180, placeholder="..."),
            "repository_summary": shorten(str(parsed.get("repository_summary", "")), width=260, placeholder="..."),
            "coverage_summary": shorten(str(parsed.get("coverage_summary", "")), width=220, placeholder="..."),
        }

    async def explain_finding(self, remediation_context: dict) -> dict:
        parsed = await self._chat_json(
            task_name="explain",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": load_prompt_pack("explain_prompt.md")},
                {"role": "user", "content": f"Remediation context JSON: {json_for_task_prompt('explain', 'remediation_context', remediation_context, max_chars=2600)}"},
            ],
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
        parsed = await self._chat_json(
            task_name="fix_draft",
            max_tokens=1536,
            messages=[
                {"role": "system", "content": load_prompt_pack("fix_prompt.md")},
                {"role": "user", "content": f"Mode: {mode}\nRemediation context JSON: {json_for_task_prompt('fix_draft', 'remediation_context', remediation_context, max_chars=2800)}"},
            ],
        )
        return {
            "review_summary": shorten(str(parsed.get("review_summary", "")), width=280, placeholder="..."),
            "recommended_strategy_id": str(parsed.get("recommended_strategy_id", "")).strip() or None,
            "strategies": [normalize_fix_strategy(item) for item in parsed.get("strategies", []) if isinstance(item, dict)],
            "patch": normalize_patch_candidate(parsed.get("patch", {})),
        }

    async def validate_remediation(self, remediation_context: dict, remediation_draft: dict, mode: str) -> dict:
        parsed = await self._chat_json(
            task_name="fix_validate",
            max_tokens=1536,
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

    async def _chat_json(self, *, task_name: str, max_tokens: int, messages: list[dict]) -> dict:
        content = await self._chat_text(task_name=task_name, max_tokens=max_tokens, messages=messages)
        parsed = extract_json(content)
        if not parsed:
            raise ExternalAIServiceError(
                "Modal returned a completion without JSON content for this task.",
                provider="modal",
                retryable=True,
                failure_kind="output_format",
            )
        return parsed

    async def _chat_text(self, *, task_name: str, max_tokens: int, messages: list[dict]) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_router.route(task_name),
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.02,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPStatusError as exc:
            detail = _modal_error_message(exc.response)
            status_code = exc.response.status_code
            retryable = status_code >= 500 or status_code in {408, 409, 429}
            failure_kind = "gateway" if status_code in {502, 503, 504} else "rate_limit" if status_code == 429 else "upstream"
            raise ExternalAIServiceError(
                detail,
                provider="modal",
                retryable=retryable,
                status_code=status_code,
                failure_kind=failure_kind,
            ) from exc
        except httpx.HTTPError as exc:
            raise ExternalAIServiceError(
                "CodeGuard could not reach the configured Modal provider. Check network access and retry.",
                provider="modal",
                retryable=True,
                failure_kind="connection",
            ) from exc

        choices = body.get("choices", [])
        if not choices:
            raise ExternalAIServiceError("Modal returned no completion choices.", provider="modal", retryable=True)
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
        reasoning = message.get("reasoning_content")
        if isinstance(reasoning, str) and "{" in reasoning and "}" in reasoning:
            return reasoning
        raise ExternalAIServiceError(
            "Modal returned a completion without usable content.",
            provider="modal",
            retryable=False,
            failure_kind="output_format",
        )


def _modal_error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"Modal provider returned HTTP {response.status_code}."
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return f"Modal provider error: {message.strip()}"
        detail = body.get("detail")
        if isinstance(detail, str) and detail.strip():
            return f"Modal provider error: {detail.strip()}"
    return f"Modal provider returned HTTP {response.status_code}."
