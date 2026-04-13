import asyncio
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.ai.agents.explain_agent import ExplainAgent
from app.infrastructure.ai.agents.fix_agent import FixAgent
from app.infrastructure.ai.agents.validation_agent import ValidationAgent
from app.infrastructure.ai.orchestration.model_router import ModelRouter
from app.infrastructure.ai.orchestration.remediation_router import RemediationRouter


class FakeAIClient:
    async def explain_finding(self, remediation_context: dict) -> dict:
        return {
            "summary": "Explained vulnerability",
            "entry_point": remediation_context["finding"]["attack_input"],
            "sink": f"{remediation_context['finding']['file']}:{remediation_context['finding']['line']}",
        }

    async def draft_fix_strategies(self, remediation_context: dict, mode: str) -> dict:
        return {
            "review_summary": f"{mode} remediation",
            "recommended_strategy_id": "parameterized-query",
            "strategies": [
                {
                    "id": "parameterized-query",
                    "label": "Parameterized query",
                    "kind": "refactor",
                    "recommended": True,
                }
            ],
            "patch": {
                "file": remediation_context["finding"]["file"],
                "diff": "--- a/x\n+++ b/x\n@@\n-old\n+new",
                "validation_notes": ["Patch targets the sink."],
            },
        }

    async def validate_remediation(self, remediation_context: dict, remediation_draft: dict, mode: str) -> dict:
        return {
            **remediation_draft,
            "patch": {
                **remediation_draft["patch"],
                "validation_notes": ["Validation completed.", "Patch still targets the sink."],
            },
        }


class MissingPatchValidationAIClient(FakeAIClient):
    async def validate_remediation(self, remediation_context: dict, remediation_draft: dict, mode: str) -> dict:
        return {
            "review_summary": remediation_draft.get("review_summary", ""),
            "recommended_strategy_id": remediation_draft.get("recommended_strategy_id"),
            "strategies": remediation_draft.get("strategies", []),
            "validation_notes": ["Validation completed."],
        }


def _context() -> dict:
    return {
        "finding": {
            "id": "finding-1",
            "title": "Dynamic query construction may allow injection",
            "category": "SQL injection",
            "severity": "high",
            "file": "app/features/login/router.py",
            "line": 43,
            "line_end": 44,
            "summary": "User-controlled input reaches a SQL sink.",
            "impact": "Authentication logic may be bypassed.",
            "attack_input": "POST /login",
            "attack_execution": "router -> service -> query builder",
            "attack_result": "SQL injection",
        },
        "code": {
            "language": "python",
            "window": {
                "start_line": 40,
                "end_line": 46,
                "snippet": "query = f\"SELECT * FROM users WHERE email = '{email}'\"\nreturn db.execute(query)",
            },
            "evidence_lines": [
                {"line": 43, "content": "query = f\"SELECT * FROM users WHERE email = '{email}'\""},
                {"line": 44, "content": "return db.execute(query)"},
            ],
        },
        "path": {
            "path_hint": "POST /login -> router -> db.execute",
            "source": {"file": "app/features/login/router.py", "line": 41},
            "sink": {"file": "app/features/login/router.py", "line": 44},
            "line_sequence": [41, 43, 44],
            "steps": [
                {"line": 41, "summary": "Read attacker-controlled email"},
                {"line": 43, "summary": "Interpolate SQL query"},
                {"line": 44, "summary": "Execute SQL statement"},
            ],
        },
        "retry": {
            "attempt": 2,
            "excluded_strategy_ids": ["manual-sanitization"],
            "attempted_strategy_ids": ["manual-sanitization"],
        },
        "batch": {
            "findings": [
                {"id": "finding-1", "title": "Dynamic query construction may allow injection", "category": "SQL injection", "file": "app/features/login/router.py"},
                {"id": "finding-2", "title": "Open redirect", "category": "Open redirect", "file": "app/features/login/router.py"},
            ]
        },
    }


class RemediationRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        client = FakeAIClient()
        self.router = RemediationRouter(
            explain_agent=ExplainAgent(client),
            fix_agent=FixAgent(client),
            validation_agent=ValidationAgent(client),
            model_router=ModelRouter(small_model="openai/gpt-oss-20b", large_model="openai/gpt-oss-120b"),
        )

    def test_trace_includes_internal_policy_and_retry_steps(self):
        context = _context()
        asyncio.run(self.router.start_run(context, "batch"))
        explanation = asyncio.run(self.router.explain(context, mode="batch"))
        asyncio.run(self.router.generate_fix(context, mode="batch"))

        trace = asyncio.run(self.router.build_trace(context, "batch"))
        task_names = [item.task_name for item in trace]

        self.assertIn("batch_plan", task_names)
        self.assertIn("fix_retry", task_names)
        self.assertIn("POST /login", explanation["request_example"])
        self.assertIn("attacker@example.com", explanation["payload_example"])
        explain_task = next(item for item in trace if item.task_name == "explain_draft")
        self.assertTrue(any("Allowed actions" in detail for detail in explain_task.details or []))
        self.assertTrue(any("minimal context package" in detail for detail in explain_task.details or []))

    def test_router_reuses_agent_memory_on_second_run(self):
        context = _context()

        asyncio.run(self.router.start_run(context, "single"))
        asyncio.run(self.router.explain(context, mode="single"))
        asyncio.run(self.router.generate_fix(context, mode="single"))

        asyncio.run(self.router.start_run(context, "single"))
        asyncio.run(self.router.explain(context, mode="single"))
        asyncio.run(self.router.generate_fix(context, mode="single"))

        trace = asyncio.run(self.router.build_trace(context, "single"))
        fix_task = next(item for item in trace if item.task_name == "fix_draft")
        self.assertTrue(any("Reused" in detail for detail in fix_task.details or []))

    def test_router_preserves_original_patch_when_validation_omits_patch_fields(self):
        client = MissingPatchValidationAIClient()
        router = RemediationRouter(
            explain_agent=ExplainAgent(client),
            fix_agent=FixAgent(client),
            validation_agent=ValidationAgent(client),
            model_router=ModelRouter(small_model="openai/gpt-oss-20b", large_model="openai/gpt-oss-120b"),
        )
        context = _context()

        asyncio.run(router.start_run(context, "single"))
        result = asyncio.run(router.generate_fix(context, mode="single"))

        self.assertIn("patch", result)
        self.assertEqual(result["patch"]["file"], "app/features/login/router.py")
        self.assertIn("+new", result["patch"]["diff"])
        self.assertIn("validation_notes", result["patch"])


if __name__ == "__main__":
    unittest.main()
