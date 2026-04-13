from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RemediationRepoCase:
    name: str
    local_path: Path
    expected_kind: str


REPO_ROOT = Path(__file__).resolve().parent / "repos"


REMEDIATION_BENCHMARK_CASES = [
    RemediationRepoCase("owasp_juice_shop", REPO_ROOT / "juice-shop", "vulnerable"),
    RemediationRepoCase("dvwa", REPO_ROOT / "DVWA", "vulnerable"),
    RemediationRepoCase("webgoat", REPO_ROOT / "WebGoat", "vulnerable"),
    RemediationRepoCase("nodegoat", REPO_ROOT / "NodeGoat", "vulnerable"),
    RemediationRepoCase("mutillidae_ii", REPO_ROOT / "mutillidae", "vulnerable"),
    RemediationRepoCase("vulhub", REPO_ROOT / "vulhub", "vulnerable"),
    RemediationRepoCase("damn_vulnerable_graphql_application", REPO_ROOT / "Damn-Vulnerable-GraphQL-Application", "vulnerable"),
]


TARGET_CATEGORY_RULES = {
    "sql injection": {
        "preferred_fix_type": "full_fix",
        "preferred_kind": "refactor",
        "must_mention_any": ["parameter", "%s", "prepared", "bind"],
        "reject_if_mentions_any": ["sanitize only"],
    },
    "command injection": {
        "preferred_fix_type": "full_fix",
        "preferred_kind": "refactor",
        "must_mention_any": ["shell", "argv", "args", "subprocess"],
        "reject_if_mentions_any": ["strip input only"],
    },
    "ssrf": {
        "preferred_fix_type": "full_fix",
        "preferred_kind": "sanitization",
        "must_mention_any": ["allowlist", "host", "urlparse", "validated"],
        "reject_if_mentions_any": ["temporary guard"],
    },
    "authentication bypass": {
        "preferred_fix_type": "full_fix",
        "preferred_kind": "refactor",
        "must_mention_any": ["token", "verify", "session", "auth"],
        "reject_if_mentions_any": ["route-only guard"],
    },
    "session misuse": {
        "preferred_fix_type": "full_fix",
        "preferred_kind": "refactor",
        "must_mention_any": ["session", "regenerate", "token", "validation"],
        "reject_if_mentions_any": ["router-only"],
    },
    "nosql injection": {
        "preferred_fix_type": "full_fix",
        "preferred_kind": "refactor",
        "must_mention_any": ["typed", "query", "operator", "allowlist", "$eq"],
        "reject_if_mentions_any": ["sanitize only"],
    },
    "open redirect": {
        "preferred_fix_type": "full_fix",
        "preferred_kind": "sanitization",
        "must_mention_any": ["allowlist", "relative", "redirect", "trusted"],
        "reject_if_mentions_any": ["temporary guard"],
    },
}


def normalize_category(category: str) -> str:
    lowered = category.strip().lower()
    for key in TARGET_CATEGORY_RULES:
        if key in lowered:
            return key
    return lowered
