import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.domain.entities.remediation import FixStrategyEntity, PatchCandidateEntity
from app.infrastructure.services.remediation_quality import assess_remediation_quality


class RemediationQualityTests(unittest.TestCase):
    def test_sql_injection_prefers_sink_level_refactor(self):
        strategies = [
            FixStrategyEntity(
                id="guard",
                label="Allowlist guard",
                kind="guard",
                confidence=82,
                impact="medium",
                effort="low",
                summary="Block suspicious characters before the query.",
                rationale="Quick mitigation.",
                diff="+if \"'\" in email:\n+    raise ValueError(\"invalid email\")",
            ),
            FixStrategyEntity(
                id="parameterized",
                label="Parameterized query",
                kind="refactor",
                confidence=90,
                impact="high",
                effort="medium",
                summary="Replace string interpolation with parameters.",
                rationale="Fix the sink.",
                diff="+query = \"SELECT * FROM users WHERE email = %s\"\n+cursor.execute(query, (email,))",
            ),
        ]
        patch = PatchCandidateEntity(
            file="app/features/login/router.py",
            language="python",
            summary="",
            diff="",
            before_snippet="",
            after_snippet="query = \"SELECT * FROM users WHERE email = %s\"\ncursor.execute(query, (email,))",
        )

        ranked, patch_entity, recommended = assess_remediation_quality(
            finding={"category": "SQL injection", "file": "app/features/login/router.py"},
            strategies=strategies,
            patch=patch,
        )

        self.assertEqual(recommended, "parameterized")
        self.assertEqual(ranked[0].fix_type, "full_fix")
        self.assertEqual(ranked[0].security_strength, "high")
        self.assertEqual(ranked[1].fix_type, "risky_workaround")
        self.assertIn("parameterization", " ".join(patch_entity.validation_notes).lower())

    def test_redirect_guard_is_not_presented_as_full_fix(self):
        strategies = [
            FixStrategyEntity(
                id="redirect-guard",
                label="Host allowlist check",
                kind="guard",
                confidence=80,
                impact="medium",
                effort="low",
                summary="Validate redirect target against an allowlist.",
                rationale="Constrain redirect targets.",
                diff="+if not target.startswith(\"/\"):\n+    raise ValueError(\"invalid redirect\")",
            )
        ]
        patch = PatchCandidateEntity(
            file="app/routes/auth.py",
            language="python",
            summary="",
            diff="",
            before_snippet="",
            after_snippet="if not target.startswith(\"/\"):\n    raise ValueError(\"invalid redirect\")",
        )

        ranked, patch_entity, _ = assess_remediation_quality(
            finding={"category": "Open redirect", "file": "app/routes/auth.py"},
            strategies=strategies,
            patch=patch,
        )

        self.assertEqual(ranked[0].fix_type, "risky_workaround")
        self.assertTrue(patch_entity.manual_review_required)
        self.assertTrue(any("redirect" in note.lower() for note in patch_entity.residual_risks + patch_entity.validation_notes))

    def test_sql_sanitization_only_is_marked_non_compliant(self):
        strategies = [
            FixStrategyEntity(
                id="sanitize",
                label="Sanitize input",
                kind="sanitization",
                confidence=91,
                impact="medium",
                effort="low",
                summary="Sanitize the email before building the query.",
                rationale="sanitize only before query execution",
                diff="+email = sanitize(email)",
            ),
            FixStrategyEntity(
                id="parameterized",
                label="Parameterized query",
                kind="refactor",
                confidence=88,
                impact="high",
                effort="medium",
                summary="Use a prepared query.",
                rationale="Parameterize at the sink.",
                diff="+query = \"SELECT * FROM users WHERE email = %s\"\n+cursor.execute(query, (email,))",
            ),
        ]
        patch = PatchCandidateEntity(
            file="app/features/login/router.py",
            language="python",
            summary="",
            diff="",
            before_snippet="",
            after_snippet="email = sanitize(email)",
        )

        ranked, patch_entity, recommended = assess_remediation_quality(
            finding={"category": "SQL injection", "file": "app/features/login/router.py"},
            strategies=strategies,
            patch=patch,
        )

        self.assertEqual(recommended, "parameterized")
        self.assertFalse(ranked[1].policy_compliant)
        self.assertIn("requires a refactor strategy", " ".join(ranked[1].policy_violations).lower())
        self.assertIn("parameterization", " ".join(patch_entity.validation_notes).lower())

    def test_auth_route_guard_is_policy_non_compliant(self):
        strategies = [
            FixStrategyEntity(
                id="route-guard",
                label="Add router guard",
                kind="guard",
                confidence=85,
                impact="medium",
                effort="low",
                summary="Reject requests that do not contain a token.",
                rationale="Add a route-only guard.",
                diff="+if not token:\n+    raise Unauthorized()",
            )
        ]
        patch = PatchCandidateEntity(
            file="app/routes/auth_router.py",
            language="python",
            summary="",
            diff="",
            before_snippet="",
            after_snippet="if not token:\n    raise Unauthorized()",
        )

        ranked, patch_entity, _ = assess_remediation_quality(
            finding={"category": "Authentication bypass", "file": "app/routes/auth_router.py"},
            strategies=strategies,
            patch=patch,
        )

        self.assertFalse(ranked[0].policy_compliant)
        self.assertEqual(ranked[0].fix_type, "risky_workaround")
        self.assertTrue(any("router boundary" in item.lower() for item in ranked[0].policy_violations))
        self.assertTrue(patch_entity.manual_review_required)

    def test_command_injection_prefers_structured_execution(self):
        strategies = [
            FixStrategyEntity(
                id="filter",
                label="Filter shell metacharacters",
                kind="sanitization",
                confidence=90,
                impact="medium",
                effort="low",
                summary="Strip dangerous shell characters before execution.",
                rationale="regex filtering only before shell execution",
                diff="+command = re.sub(r\"[^a-z0-9 ]\", \"\", command)\n+subprocess.run(command, shell=True)",
            ),
            FixStrategyEntity(
                id="argv",
                label="Use argv execution",
                kind="refactor",
                confidence=88,
                impact="high",
                effort="medium",
                summary="Replace shell execution with argv-based subprocess invocation.",
                rationale="Run the command as an argv list with shell=False.",
                diff="+subprocess.run([\"/usr/bin/id\", user_id], shell=False)",
            ),
        ]
        patch = PatchCandidateEntity(
            file="app/services/runner.py",
            language="python",
            summary="",
            diff="",
            before_snippet="",
            after_snippet="subprocess.run([\"/usr/bin/id\", user_id], shell=False)",
        )

        ranked, patch_entity, recommended = assess_remediation_quality(
            finding={"category": "Command injection", "file": "app/services/runner.py"},
            strategies=strategies,
            patch=patch,
        )

        self.assertEqual(recommended, "argv")
        self.assertEqual(ranked[0].fix_type, "full_fix")
        self.assertFalse(ranked[1].policy_compliant)
        self.assertTrue(any("structured argument-based execution" in note.lower() for note in patch_entity.validation_notes))

    def test_ssrf_prefers_host_validation_and_network_controls(self):
        strategies = [
            FixStrategyEntity(
                id="prefix",
                label="Allow http prefix",
                kind="guard",
                confidence=84,
                impact="medium",
                effort="low",
                summary="Require the URL to start with https.",
                rationale="string prefix check only",
                diff="+if not callback.startswith(\"https://\"):\n+    raise ValueError(\"invalid\")",
            ),
            FixStrategyEntity(
                id="allowlist",
                label="Validate destination host",
                kind="refactor",
                confidence=89,
                impact="high",
                effort="medium",
                summary="Parse the URL, block private IPs, and enforce a host allowlist before the HTTP client runs.",
                rationale="Use urlparse, ipaddress checks, and outbound allowlist enforcement in the client path.",
                diff="+parsed = urlparse(callback)\n+host_ip = ipaddress.ip_address(resolve_host(parsed.hostname))\n+if host_ip.is_private:\n+    raise ValueError(\"blocked\")",
            ),
        ]
        patch = PatchCandidateEntity(
            file="app/clients/webhook.py",
            language="python",
            summary="",
            diff="",
            before_snippet="",
            after_snippet="parsed = urlparse(callback)",
        )

        ranked, patch_entity, recommended = assess_remediation_quality(
            finding={"category": "Server-side request forgery", "file": "app/clients/webhook.py"},
            strategies=strategies,
            patch=patch,
        )

        self.assertEqual(recommended, "allowlist")
        self.assertEqual(ranked[0].fix_type, "full_fix")
        self.assertFalse(ranked[1].policy_compliant)
        self.assertTrue(any("outbound" in note.lower() or "allowlist" in note.lower() for note in patch_entity.validation_notes))

    def test_nosql_prefers_typed_filter_over_operator_screening(self):
        strategies = [
            FixStrategyEntity(
                id="screen",
                label="Screen mongo operators",
                kind="sanitization",
                confidence=87,
                impact="medium",
                effort="low",
                summary="Strip mongo operators from the user filter.",
                rationale="sanitize only before executing the query",
                diff="+user_filter = mongo_sanitize(user_filter)",
            ),
            FixStrategyEntity(
                id="typed-filter",
                label="Build typed query document",
                kind="refactor",
                confidence=91,
                impact="high",
                effort="medium",
                summary="Construct a typed filter document and pin user values into $eq clauses.",
                rationale="Use a typed filter document with operator allowlisting and $eq.",
                diff="+query = {\"username\": {\"$eq\": username}}\n+return users.find(query)",
            ),
        ]
        patch = PatchCandidateEntity(
            file="app/dao/users.js",
            language="javascript",
            summary="",
            diff="",
            before_snippet="",
            after_snippet="query = {\"username\": {\"$eq\": username}}",
        )

        ranked, patch_entity, recommended = assess_remediation_quality(
            finding={"category": "NoSQL injection", "file": "app/dao/users.js"},
            strategies=strategies,
            patch=patch,
        )

        self.assertEqual(recommended, "typed-filter")
        self.assertEqual(ranked[0].fix_type, "full_fix")
        self.assertFalse(ranked[1].policy_compliant)
        self.assertTrue(any("typed filters" in note.lower() or "operator" in note.lower() for note in patch_entity.validation_notes + patch_entity.residual_risks))

    def test_session_fixation_prefers_rotation_in_session_logic(self):
        strategies = [
            FixStrategyEntity(
                id="cookie-flags",
                label="Set secure cookies",
                kind="guard",
                confidence=82,
                impact="medium",
                effort="low",
                summary="Tighten cookie flags after login.",
                rationale="cookie flag only",
                diff="+session_cookie_secure = True",
            ),
            FixStrategyEntity(
                id="rotate-session",
                label="Rotate session id on login",
                kind="refactor",
                confidence=90,
                impact="high",
                effort="medium",
                summary="Regenerate the session identifier and invalidate the prior session after successful authentication.",
                rationale="Rotate the session and revoke the old server-side state in auth logic.",
                diff="+request.session.regenerate()\n+session.invalidate()",
            ),
        ]
        patch = PatchCandidateEntity(
            file="app/auth/session_service.py",
            language="python",
            summary="",
            diff="",
            before_snippet="",
            after_snippet="request.session.regenerate()",
        )

        ranked, patch_entity, recommended = assess_remediation_quality(
            finding={"category": "Session fixation", "file": "app/auth/session_service.py"},
            strategies=strategies,
            patch=patch,
        )

        self.assertEqual(recommended, "rotate-session")
        self.assertEqual(ranked[0].fix_type, "full_fix")
        self.assertFalse(ranked[1].policy_compliant)
        self.assertTrue(any("session" in note.lower() for note in patch_entity.validation_notes))


if __name__ == "__main__":
    unittest.main()
