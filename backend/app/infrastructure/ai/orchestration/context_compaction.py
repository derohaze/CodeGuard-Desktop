from __future__ import annotations

import json


COMPACTION_POLICIES = {
    "context_shape": {"list_limit": 4, "string_limit": 180},
    "batch_plan": {"list_limit": 6, "string_limit": 200},
    "explain": {"list_limit": 6, "string_limit": 220},
    "fix_draft": {"list_limit": 8, "string_limit": 320},
    "fix_retry": {"list_limit": 6, "string_limit": 280},
    "fix_validate": {"list_limit": 8, "string_limit": 320},
    "final_patch": {"list_limit": 5, "string_limit": 220},
}


def compact_agent_payload(task_name: str, payload: dict, *, draft: dict | None = None, memory: dict | None = None) -> tuple[dict, dict]:
    policy = COMPACTION_POLICIES.get(task_name, {"list_limit": 6, "string_limit": 220})
    compacted = {
        "finding": _shape_finding(payload.get("finding", {})),
        "code": _shape_code(payload.get("code", {}), string_limit=policy["string_limit"]),
        "path": _shape_path(payload.get("path", {}), list_limit=policy["list_limit"], string_limit=policy["string_limit"]),
    }
    if isinstance(payload.get("retry"), dict):
        compacted["retry"] = _shape_retry(payload["retry"], list_limit=policy["list_limit"], string_limit=policy["string_limit"])
    if isinstance(payload.get("batch"), dict):
        compacted["batch"] = _shape_batch(payload["batch"], list_limit=policy["list_limit"], string_limit=policy["string_limit"])
    if memory and memory.get("hit"):
        compacted["agent_memory"] = {
            "scope_key": memory.get("scope_key", ""),
            "entry_count": memory.get("entry_count", 0),
            "latest": memory.get("latest", {}),
        }
    if draft is not None:
        compacted["draft"] = _shape_draft(draft, list_limit=policy["list_limit"], string_limit=policy["string_limit"])

    original_chars = _char_count(payload if draft is None else {"context": payload, "draft": draft})
    compacted_chars = _char_count(compacted)
    stats = {
        "policy": task_name,
        "original_chars": original_chars,
        "compacted_chars": compacted_chars,
        "reduction_percent": max(0, min(100, round((1 - (compacted_chars / max(1, original_chars))) * 100))),
    }
    return compacted, stats


def _shape_finding(finding: dict) -> dict:
    if not isinstance(finding, dict):
        return {}
    return {
        "id": str(finding.get("id", "")),
        "title": str(finding.get("title", "")),
        "category": str(finding.get("category", "")),
        "severity": str(finding.get("severity", "")),
        "file": str(finding.get("file", "")),
        "line": int(finding.get("line", 0) or 0),
        "line_end": int(finding.get("line_end", finding.get("line", 0)) or 0),
        "confidence": int(finding.get("confidence", 0) or 0),
        "summary": str(finding.get("summary", ""))[:220],
        "impact": str(finding.get("impact", ""))[:220],
        "evidence": str(finding.get("evidence", ""))[: max(120, 220)],
        "explanation": str(finding.get("explanation", ""))[:220],
        "attack_input": str(finding.get("attack_input", ""))[:180],
        "attack_execution": str(finding.get("attack_execution", ""))[:220],
        "attack_result": str(finding.get("attack_result", ""))[:180],
    }


def _shape_code(code: dict, *, string_limit: int) -> dict:
    if not isinstance(code, dict):
        return {}
    window = code.get("window", {}) if isinstance(code.get("window"), dict) else {}
    source_window = code.get("source_window", {}) if isinstance(code.get("source_window"), dict) else {}
    sink_window = code.get("sink_window", {}) if isinstance(code.get("sink_window"), dict) else {}
    return {
        "file": str(code.get("file", "")),
        "language": str(code.get("language", "")),
        "window": {
            "start_line": int(window.get("start_line", 0) or 0),
            "end_line": int(window.get("end_line", 0) or 0),
            "snippet": str(window.get("snippet", ""))[: max(80, string_limit * 3)],
        },
        "evidence_lines": [
            {
                "line": int(item.get("line", 0) or 0),
                "content": str(item.get("content", ""))[:string_limit],
            }
            for item in code.get("evidence_lines", [])[:8]
            if isinstance(item, dict)
        ],
        "source_window": {
            "file": str(source_window.get("file", "")),
            "line_start": int(source_window.get("line_start", 0) or 0),
            "line_end": int(source_window.get("line_end", 0) or 0),
            "snippet": str(source_window.get("snippet", ""))[: max(80, string_limit * 2)],
        }
        if source_window
        else None,
        "sink_window": {
            "file": str(sink_window.get("file", "")),
            "line_start": int(sink_window.get("line_start", 0) or 0),
            "line_end": int(sink_window.get("line_end", 0) or 0),
            "snippet": str(sink_window.get("snippet", ""))[: max(80, string_limit * 2)],
        }
        if sink_window
        else None,
    }


def _shape_path(path: dict, *, list_limit: int, string_limit: int) -> dict:
    if not isinstance(path, dict):
        return {}
    return {
        "summary": {
            "path_hint": str(path.get("path_hint", ""))[:string_limit],
            "source": path.get("source"),
            "sink": path.get("sink"),
            "line_sequence": path.get("line_sequence", [])[:list_limit],
        },
        "steps": [
            {
                "line": int(item.get("line", 0) or 0),
                "summary": str(item.get("summary", item.get("content", "")))[:string_limit],
            }
            for item in path.get("steps", [])[:list_limit]
            if isinstance(item, dict)
        ],
    }


def _shape_retry(retry: dict, *, list_limit: int, string_limit: int) -> dict:
    return {
        "attempt": int(retry.get("attempt", 1) or 1),
        "excluded_strategy_ids": [str(item)[:string_limit] for item in retry.get("excluded_strategy_ids", [])[:list_limit]],
        "attempted_strategy_ids": [str(item)[:string_limit] for item in retry.get("attempted_strategy_ids", [])[:list_limit]],
        "previous_failures": [
            {
                "chosen_strategy": str(item.get("chosen_strategy", ""))[:string_limit],
                "expected_strategy": str(item.get("expected_strategy", ""))[:string_limit],
                "score_total": int(item.get("score_total", 0) or 0),
            }
            for item in retry.get("previous_failures", [])[:list_limit]
            if isinstance(item, dict)
        ],
    }


def _shape_batch(batch: dict, *, list_limit: int, string_limit: int) -> dict:
    return {
        "findings": [
            {
                "id": str(item.get("id", "")),
                "title": str(item.get("title", ""))[:string_limit],
                "category": str(item.get("category", ""))[:string_limit],
                "file": str(item.get("file", ""))[:string_limit],
            }
            for item in batch.get("findings", [])[:list_limit]
            if isinstance(item, dict)
        ]
    }


def _shape_draft(draft: dict, *, list_limit: int, string_limit: int) -> dict:
    if not isinstance(draft, dict):
        return {}
    patch = draft.get("patch", {}) if isinstance(draft.get("patch"), dict) else {}
    return {
        "review_summary": str(draft.get("review_summary", ""))[:string_limit],
        "recommended_strategy_id": str(draft.get("recommended_strategy_id", ""))[:string_limit],
        "strategies": [
            {
                "id": str(item.get("id", ""))[:string_limit],
                "label": str(item.get("label", ""))[:string_limit],
                "kind": str(item.get("kind", ""))[:string_limit],
                "summary": str(item.get("summary", ""))[:string_limit],
                "rationale": str(item.get("rationale", ""))[: max(120, string_limit * 2)],
                "diff": str(item.get("diff", ""))[: max(200, string_limit * 3)],
                "recommended": bool(item.get("recommended", False)),
            }
            for item in draft.get("strategies", [])[:list_limit]
            if isinstance(item, dict)
        ],
        "patch": {
            "file": str(patch.get("file", ""))[:string_limit],
            "summary": str(patch.get("summary", ""))[:string_limit],
            "diff": str(patch.get("diff", ""))[: max(200, string_limit * 4)],
            "validation_notes": [str(item)[:string_limit] for item in patch.get("validation_notes", [])[:list_limit]],
            "before_snippet": str(patch.get("before_snippet", ""))[: max(120, string_limit * 3)],
            "after_snippet": str(patch.get("after_snippet", ""))[: max(120, string_limit * 3)],
        },
    }


def _char_count(value: object) -> int:
    try:
        return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    except TypeError:
        return len(str(value))
