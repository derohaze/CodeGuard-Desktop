from pathlib import Path
import sys
import tempfile
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.repository.framework_detection import detect_framework_profile
from app.infrastructure.services.repository.repository_analysis import build_repository_profile
from app.infrastructure.services.repository.repository_graph import build_repository_graph


class RepositoryGraphTests(unittest.TestCase):
    def test_builds_framework_profile_and_graph_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "main.py").write_text(
                "from fastapi import FastAPI\n"
                "from services.runner import run_job\n"
                "app = FastAPI()\n"
                "@app.post('/scan')\n"
                "async def scan(payload: dict):\n"
                "    return run_job(payload)\n",
                encoding="utf-8",
            )
            (root / "services").mkdir()
            (root / "services" / "runner.py").write_text(
                "def run_job(payload):\n"
                "    return payload\n",
                encoding="utf-8",
            )
            files = [root / "main.py", root / "services" / "runner.py"]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)

            self.assertEqual(framework_profile["primary_framework"], "fastapi")
            self.assertGreaterEqual(graph["summary"]["import_edges"], 1)
            self.assertEqual(graph["summary"]["route_files"], 1)

    def test_detects_java_servlet_framework_and_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "example").mkdir(parents=True)
            servlet = root / "src" / "example" / "LoginServlet.java"
            servlet.write_text(
                "package example;\n"
                "import javax.servlet.http.HttpServlet;\n"
                "import javax.servlet.http.HttpServletRequest;\n"
                "import javax.servlet.http.HttpServletResponse;\n"
                "public class LoginServlet extends HttpServlet {\n"
                "  protected void doPost(HttpServletRequest request, HttpServletResponse response) {}\n"
                "}\n",
                encoding="utf-8",
            )
            files = [servlet]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)

            self.assertEqual(framework_profile["primary_framework"], "java_servlet")
            self.assertEqual(graph["summary"]["route_files"], 1)

    def test_detects_graphql_framework_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graphql_file = root / "views.py"
            graphql_file.write_text(
                "import graphene\n"
                "from flask import Flask\n"
                "app = Flask(__name__)\n"
                "class Query(graphene.ObjectType):\n"
                "    ping = graphene.String(arg=graphene.String())\n"
                "schema = graphene.Schema(query=Query)\n"
                "app.add_url_rule('/graphql', view_func=lambda: None)\n",
                encoding="utf-8",
            )
            files = [graphql_file]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)

            self.assertEqual(framework_profile["primary_framework"], "graphql")

    def test_detects_graphql_apollo_profile_and_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graphql_file = root / "server.ts"
            graphql_file.write_text(
                "import { ApolloServer } from '@apollo/server';\n"
                "const typeDefs = `type Query { ping(input: String): String }`;\n"
                "const resolvers = { Query: { ping: (_p, args) => args.input } };\n"
                "const server = new ApolloServer({ typeDefs, resolvers });\n",
                encoding="utf-8",
            )
            files = [graphql_file]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)

            self.assertEqual(framework_profile["primary_framework"], "graphql")
            self.assertEqual(graph["summary"]["route_files"], 1)

    def test_detects_jsp_servlet_route_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jsp = root / "login.jsp"
            jsp.write_text(
                "<%@ page language=\"java\" %>\n"
                "<% String user = request.getParameter(\"user\"); %>\n"
                "<jsp:forward page=\"/secure/home.jsp\" />\n",
                encoding="utf-8",
            )
            files = [jsp]
            profile = build_repository_profile(root, files)
            framework_profile = detect_framework_profile(root, files, profile)
            graph = build_repository_graph(root, files, framework_profile)

            self.assertIn("java_servlet", framework_profile["frameworks"])
            self.assertEqual(graph["summary"]["route_files"], 1)


if __name__ == "__main__":
    unittest.main()
