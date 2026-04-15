import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.domain.entities.remediation import FixStrategyEntity, PatchCandidateEntity
from app.infrastructure.services.remediation.remediation_scoring import score_remediation


class RemediationScoringTests(unittest.TestCase):
    def test_sql_parameterization_scores_higher_than_guard(self):
        full_fix = score_remediation(
            finding={"category": "SQL injection", "file": "app/routes/login.py"},
            strategy=FixStrategyEntity(
                id="s1",
                label="Parameterized query",
                kind="refactor",
                confidence=92,
                impact="high",
                effort="medium",
                summary="",
                rationale="",
                diff="cursor.execute(query, (email,))",
                recommended=True,
                fix_type="full_fix",
                security_strength="high",
                regression_risk="medium",
            ),
            patch=PatchCandidateEntity(
                file="app/routes/login.py",
                language="python",
                summary="",
                diff="",
                validation_notes=["Fully mitigates the SQL injection at the sink."],
                before_snippet="",
                after_snippet="cursor.execute(query, (email,))",
                fix_type="full_fix",
                residual_risks=["No residual injection risk remains in this file."],
            ),
        )
        guard_fix = score_remediation(
            finding={"category": "SQL injection", "file": "app/routes/login.py"},
            strategy=FixStrategyEntity(
                id="s2",
                label="Input guard",
                kind="guard",
                confidence=78,
                impact="medium",
                effort="low",
                summary="",
                rationale="",
                diff="if \"'\" in email: raise ValueError",
                recommended=False,
                fix_type="temporary_guard",
                security_strength="low",
                regression_risk="low",
            ),
            patch=PatchCandidateEntity(
                file="app/routes/login.py",
                language="python",
                summary="",
                diff="",
                validation_notes=["Temporary guard only."],
                before_snippet="",
                after_snippet="if \"'\" in email: raise ValueError",
                fix_type="temporary_guard",
                residual_risks=["The sink still deserves parameterization at the query execution layer."],
            ),
        )

        self.assertGreater(full_fix.total, guard_fix.total)
        self.assertGreater(full_fix.fix_completeness, guard_fix.fix_completeness)
        self.assertGreater(full_fix.strategy_quality, guard_fix.strategy_quality)

    def test_sql_non_full_fix_cannot_score_high_after_enforcement(self):
        weak_fix = score_remediation(
            finding={"category": "SQL injection", "file": "app/routes/login.py"},
            strategy=FixStrategyEntity(
                id="s3",
                label="Sanitize email",
                kind="sanitization",
                confidence=95,
                impact="medium",
                effort="low",
                summary="Sanitize the email before the query.",
                rationale="sanitize only before query execution",
                diff="email = sanitize(email)",
                recommended=True,
                fix_type="partial_mitigation",
                security_strength="medium",
                regression_risk="low",
                policy_compliant=False,
                policy_violations=["This vulnerability requires a refactor strategy, not sanitization."],
            ),
            patch=PatchCandidateEntity(
                file="app/routes/login.py",
                language="python",
                summary="",
                diff="",
                validation_notes=["Sanitizes the input before query execution."],
                before_snippet="",
                after_snippet="email = sanitize(email)",
                fix_type="partial_mitigation",
                residual_risks=["The sink still deserves parameterization at the query execution layer."],
            ),
        )

        self.assertLessEqual(weak_fix.total, 54)
        self.assertLessEqual(weak_fix.fix_completeness, 34)
        self.assertTrue(any("hard enforcement" in item.lower() for item in weak_fix.rationale))


if __name__ == "__main__":
    unittest.main()
