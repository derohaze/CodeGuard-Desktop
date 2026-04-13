from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.remediation import FixStrategyEntity


@dataclass(frozen=True, slots=True)
class PolicyRule:
    preferred_fix_type: str
    preferred_kind: str
    must_mention_any: tuple[str, ...]
    reject_if_mentions_any: tuple[str, ...]
    enforce_sink_level: bool = False
    forbid_router_only: bool = False


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    compliant: bool
    violations: tuple[str, ...]
    required_fix_type: str | None
    required_kind: str | None


RULES: dict[str, PolicyRule] = {
    "sql injection": PolicyRule(
        preferred_fix_type="full_fix",
        preferred_kind="refactor",
        must_mention_any=("parameter", "%s", "prepared", "bind"),
        reject_if_mentions_any=("sanitize only", "escape quotes", "strip dangerous chars"),
        enforce_sink_level=True,
    ),
    "command injection": PolicyRule(
        preferred_fix_type="full_fix",
        preferred_kind="refactor",
        must_mention_any=(
            "subprocess.run(",
            "subprocess.popen(",
            "execfile",
            "spawn(",
            "argv",
            "args",
            "array command",
            "shell=false",
            "shell false",
            "no shell",
        ),
        reject_if_mentions_any=(
            "strip input only",
            "regex filtering only",
            "escape shell chars only",
            "shell=true",
            "sh -c",
            "bash -c",
        ),
        enforce_sink_level=True,
    ),
    "ssrf": PolicyRule(
        preferred_fix_type="full_fix",
        preferred_kind="refactor",
        must_mention_any=(
            "allowlist",
            "hostname",
            "host",
            "urlparse",
            "urlsplit",
            "scheme",
            "ipaddress",
            "private ip",
            "metadata",
            "outbound",
            "egress",
            "validated",
        ),
        reject_if_mentions_any=(
            "temporary guard",
            "regex only",
            "startswith(\"http",
            "startswith('http",
            "string prefix check only",
        ),
        enforce_sink_level=True,
    ),
    "authentication bypass": PolicyRule(
        preferred_fix_type="full_fix",
        preferred_kind="refactor",
        must_mention_any=("token", "verify", "session", "auth", "signature", "claims", "principal", "securitycontext"),
        reject_if_mentions_any=("route-only guard", "middleware-only", "presence check only", "token exists only"),
        forbid_router_only=True,
    ),
    "session misuse": PolicyRule(
        preferred_fix_type="full_fix",
        preferred_kind="refactor",
        must_mention_any=("session", "regenerate", "rotation", "invalidate", "revoke", "token", "validation"),
        reject_if_mentions_any=("router-only", "cookie flag only", "csrf only", "header check only"),
        forbid_router_only=True,
    ),
    "nosql injection": PolicyRule(
        preferred_fix_type="full_fix",
        preferred_kind="refactor",
        must_mention_any=("typed", "query", "operator", "allowlist", "$eq", "bson", "filter document", "query builder"),
        reject_if_mentions_any=("sanitize only", "regex strip only", "$where", "$regex", "escape mongo chars only"),
        enforce_sink_level=True,
    ),
    "open redirect": PolicyRule(
        preferred_fix_type="full_fix",
        preferred_kind="sanitization",
        must_mention_any=("allowlist", "relative", "redirect", "trusted"),
        reject_if_mentions_any=("temporary guard",),
    ),
}

ALIASES = {
    "server-side request forgery": "ssrf",
    "server side request forgery": "ssrf",
    "session fixation": "session misuse",
    "session hijacking": "session misuse",
    "authorization bypass": "authentication bypass",
    "auth bypass": "authentication bypass",
    "no sql injection": "nosql injection",
}


def normalize_category(category: str) -> str:
    lowered = category.strip().lower()
    for alias, canonical in ALIASES.items():
        if alias in lowered:
            return canonical
    for key in sorted(RULES, key=len, reverse=True):
        if key in lowered:
            return key
    return lowered


def rule_for_category(category: str) -> PolicyRule | None:
    return RULES.get(normalize_category(category))


def category_requires_full_fix(category: str) -> bool:
    rule = rule_for_category(category)
    return bool(rule and rule.preferred_fix_type == "full_fix")


def evaluate_strategy_policy(
    *,
    category: str,
    strategy: FixStrategyEntity,
    fix_type: str,
    patch_file: str,
) -> PolicyEvaluation:
    rule = rule_for_category(category)
    if rule is None:
        return PolicyEvaluation(True, (), None, None)

    text = " ".join(
        (
            strategy.label,
            strategy.summary,
            strategy.rationale,
            strategy.diff,
            strategy.selection_reason,
        )
    ).lower()
    patch_file_lower = patch_file.replace("\\", "/").lower()
    violations: list[str] = []

    if rule.preferred_kind and strategy.kind != rule.preferred_kind:
        violations.append(f"This vulnerability requires a {rule.preferred_kind} strategy, not {strategy.kind}.")
    if rule.preferred_fix_type and fix_type != rule.preferred_fix_type:
        violations.append(
            f"This vulnerability requires a {rule.preferred_fix_type.replace('_', ' ')} instead of {fix_type.replace('_', ' ')}."
        )
    if rule.must_mention_any and not any(token in text for token in rule.must_mention_any):
        violations.append("The proposed strategy does not include the required sink-level remediation shape for this category.")
    if rule.reject_if_mentions_any and any(token in text for token in rule.reject_if_mentions_any):
        violations.append("The proposed strategy matches a previously rejected weak remediation family.")
    if rule.enforce_sink_level and strategy.kind != "refactor":
        violations.append("The fix must eliminate the injection vector at the sink instead of screening input earlier in the path.")
    if rule.forbid_router_only and "router" in patch_file_lower:
        violations.append("The fix must move into central auth/session logic rather than staying only at the router boundary.")

    return PolicyEvaluation(
        compliant=not violations,
        violations=tuple(violations),
        required_fix_type=rule.preferred_fix_type,
        required_kind=rule.preferred_kind,
    )
