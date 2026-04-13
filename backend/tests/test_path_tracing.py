from pathlib import Path
import sys
import tempfile
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.framework_detection import detect_framework_profile
from app.infrastructure.services.path_tracing import trace_candidate_paths
from app.infrastructure.services.repository_analysis import build_repository_profile
from app.infrastructure.services.repository_graph import build_repository_graph
from app.infrastructure.services.source_sink_registry import build_source_sink_registry


class PathTracingTests(unittest.TestCase):
    def test_traces_intra_file_symbol_flow_with_python_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = root / "handler.py"
            sample.write_text(
                "import subprocess\n"
                "from fastapi import Request\n"
                "async def route(request: Request):\n"
                "    payload = await request.body()\n"
                "    command = payload.decode()\n"
                "    return subprocess.run(command, shell=True)\n",
                encoding="utf-8",
            )
            files = [sample]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertGreaterEqual(traced["summary"]["candidate_path_count"], 1)
            self.assertTrue(any(item["path_type"] == "intra_file" for item in traced["paths"]))
            self.assertTrue(any(len(item["line_sequence"]) >= 2 for item in traced["paths"]))

    def test_traces_cross_file_source_to_sink_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "routes.py").write_text(
                "from fastapi import Request\n"
                "from service import handle\n"
                "async def route(request: Request):\n"
                "    payload = request.json\n"
                "    return handle(payload)\n",
                encoding="utf-8",
            )
            (root / "service.py").write_text(
                "import subprocess\n"
                "def handle(payload):\n"
                "    return subprocess.run(payload, shell=True)\n",
                encoding="utf-8",
            )
            files = [root / "routes.py", root / "service.py"]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertGreaterEqual(traced["summary"]["candidate_path_count"], 1)
            self.assertTrue(any(item["path_type"] == "cross_file" for item in traced["paths"]))

    def test_marks_sanitized_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = root / "safe_handler.py"
            sample.write_text(
                "import os\n"
                "from fastapi import Request\n"
                "async def route(request: Request):\n"
                "    payload = await request.body()\n"
                "    safe_path = os.path.normpath(payload.decode())\n"
                "    return open(safe_path)\n",
                encoding="utf-8",
            )
            files = [sample]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertTrue(any(item["has_sanitizer"] for item in traced["paths"]))
            self.assertGreaterEqual(traced["summary"]["sanitized_paths"], 1)

    def test_traces_java_servlet_to_jdbc_cross_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "example").mkdir(parents=True)
            servlet = root / "src" / "example" / "LoginServlet.java"
            dbutil = root / "src" / "example" / "DBUtil.java"
            servlet.write_text(
                "package example;\n"
                "import javax.servlet.http.HttpServlet;\n"
                "import javax.servlet.http.HttpServletRequest;\n"
                "import javax.servlet.http.HttpServletResponse;\n"
                "import example.DBUtil;\n"
                "public class LoginServlet extends HttpServlet {\n"
                "  protected void doPost(HttpServletRequest request, HttpServletResponse response) {\n"
                "    String user = request.getParameter(\"uid\");\n"
                "    DBUtil.lookup(user);\n"
                "  }\n"
                "}\n",
                encoding="utf-8",
            )
            dbutil.write_text(
                "package example;\n"
                "public class DBUtil {\n"
                "  public static void lookup(String user) {\n"
                "    statement.executeQuery(\"SELECT * FROM PEOPLE WHERE USER='\" + user + \"'\");\n"
                "  }\n"
                "}\n",
                encoding="utf-8",
            )
            files = [servlet, dbutil]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertTrue(any(item["path_type"] == "cross_file" for item in traced["paths"]))
            self.assertGreaterEqual(traced["summary"]["candidate_path_count"], 1)

    def test_traces_graphql_resolver_input_to_command_sink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = root / "views.py"
            sample.write_text(
                "import graphene\n"
                "from core import helpers\n"
                "class Query(graphene.ObjectType):\n"
                "  system_debug = graphene.String(arg=graphene.String())\n"
                "  def resolve_system_debug(self, info, arg=None):\n"
                "    return helpers.run_cmd('ps {}'.format(arg))\n",
                encoding="utf-8",
            )
            files = [sample]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertGreaterEqual(traced["summary"]["candidate_path_count"], 1)

    def test_traces_js_graphql_resolver_to_raw_query_sink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = root / "resolver.ts"
            sample.write_text(
                "import { ApolloServer } from '@apollo/server';\n"
                "export const resolvers = {\n"
                "  Query: {\n"
                "    users: async (_parent, args, context) => sequelize.query(`select * from users where email = '${args.email}'`),\n"
                "  },\n"
                "};\n",
                encoding="utf-8",
            )
            files = [sample]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertGreaterEqual(traced["summary"]["candidate_path_count"], 1)

    def test_traces_multi_service_source_to_downstream_sink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "frontend").mkdir(parents=True)
            (root / "src" / "paymentservice").mkdir(parents=True)
            frontend = root / "src" / "frontend" / "main.go"
            payment = root / "src" / "paymentservice" / "server.go"
            frontend.write_text(
                "package main\n"
                "import \"os\"\n"
                "func handler(r *Request) {\n"
                "  target := r.FormValue(\"target\")\n"
                "  paymentAddr := os.Getenv(\"PAYMENT_SERVICE_ADDR\")\n"
                "  grpc.Dial(paymentAddr)\n"
                "  _ = target\n"
                "}\n",
                encoding="utf-8",
            )
            payment.write_text(
                "package main\n"
                "func call(target string) {\n"
                "  http.Get(target)\n"
                "}\n",
                encoding="utf-8",
            )
            files = [frontend, payment]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertGreaterEqual(graph["summary"]["service_edges"], 1)
            self.assertGreaterEqual(traced["summary"]["candidate_path_count"], 1)
            self.assertTrue(any(item["path_type"] == "cross_file" for item in traced["paths"]))

    def test_traces_go_http_handler_to_service_sink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = root / "main.go"
            sample.write_text(
                "package main\n"
                "import \"google.golang.org/grpc\"\n"
                "func main() {\n"
                "  r.HandleFunc(\"/cart\", addToCartHandler)\n"
                "  grpc.NewClient(cartAddr)\n"
                "}\n",
                encoding="utf-8",
            )
            files = [sample]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)
            registry = build_source_sink_registry(root, files, framework_profile)
            traced = trace_candidate_paths(root, graph, registry, files)

            self.assertGreaterEqual(traced["summary"]["candidate_path_count"], 1)


if __name__ == "__main__":
    unittest.main()
