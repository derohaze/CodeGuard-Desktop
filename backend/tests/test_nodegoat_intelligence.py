from pathlib import Path
import sys
import tempfile
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.repository.framework_detection import detect_framework_profile
from app.infrastructure.services.repository.path_tracing import trace_candidate_paths
from app.infrastructure.services.repository.repository_analysis import build_repository_profile, run_precise_heuristics
from app.infrastructure.services.repository.repository_graph import build_repository_graph
from app.infrastructure.services.repository.source_sink_registry import build_source_sink_registry


class NodeGoatIntelligenceTests(unittest.TestCase):
    def test_node_registry_prefers_real_sinks_over_require_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            route = root / "route.js"
            route.write_text(
                'const dao = require("./dao");\n'
                "function handler(req, res) {\n"
                "  return res.redirect(req.query.url);\n"
                "}\n",
                encoding="utf-8",
            )
            files = [route]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            registry = build_source_sink_registry(root, files, framework_profile)

            sink_kinds = {item["kind"] for item in registry["sinks"]}
            self.assertIn("outbound_request", sink_kinds)
            self.assertNotIn("filesystem_access", sink_kinds)

    def test_node_cross_file_path_reaches_nosql_sink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "routes.js").write_text(
                'const dao = require("./dao");\n'
                "function handler(req, res) {\n"
                "  return dao.lookup(req.query.threshold);\n"
                "}\n",
                encoding="utf-8",
            )
            (root / "dao.js").write_text(
                "function lookup(threshold) {\n"
                "  return db.collection('allocations').find({ $where: `this.stocks > '${threshold}'` });\n"
                "}\n",
                encoding="utf-8",
            )
            files = [root / "routes.js", root / "dao.js"]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertGreaterEqual(traced["summary"]["candidate_path_count"], 1)
            self.assertTrue(any(item["path_type"] == "cross_file" for item in traced["paths"]))

    def test_nodegoat_heuristics_detect_core_node_signals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = root / "app.js"
            sample.write_text(
                "this.handleLoginRequest = (req, res) => {};\n"
                "const isAdmin = sessionHandler.isAdminUserMiddleware;\n"
                "app.get('/allocations/:userId', isLoggedIn, allocationsHandler.displayAllocations);\n"
                "app.get('/benefits', isLoggedIn, benefitsHandler.displayBenefits);\n"
                "app.post('/benefits', isLoggedIn, benefitsHandler.updateBenefits);\n"
                "const preTax = eval(req.body.preTax);\n"
                "return res.redirect(req.query.url);\n"
                "req.session.userId = user._id;\n",
                encoding="utf-8",
            )

            findings = run_precise_heuristics(sample, sample.read_text(encoding="utf-8"), root)
            titles = {item["title"] for item in findings}

            self.assertIn("User-controlled input reaches eval()", titles)
            self.assertIn("User-controlled redirect target may enable open redirect", titles)
            self.assertIn("Session state changes without regeneration after login", titles)
            self.assertIn("Route trusts attacker-controlled object reference", titles)
            self.assertIn("Privileged route appears reachable without role enforcement", titles)


if __name__ == "__main__":
    unittest.main()
