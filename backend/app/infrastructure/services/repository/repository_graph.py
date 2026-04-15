import re
from pathlib import Path

from app.infrastructure.services.repository.auth_detection import detect_auth_boundaries
from app.infrastructure.services.repository.call_graph import build_call_graph
from app.infrastructure.services.repository.python_flow_analysis import analyze_python_file
from app.infrastructure.services.repository.service_graph import build_service_graph
from app.infrastructure.services.repository.repository_analysis import (
    detect_route_summary,
    parse_imports,
    read_text,
    relative_path,
)


CALL_PATTERN = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
AUTH_KEYWORDS = ("auth", "jwt", "token", "session", "login", "bearer")


def build_repository_graph(source_root: Path, files: list[Path], framework_profile: dict) -> dict:
    import_edges: list[dict] = []
    route_nodes: list[dict] = []
    auth_nodes: list[dict] = detect_auth_boundaries(source_root, files)

    internal_files = {
        relative_path(path, source_root): path
        for path in files
        if path.suffix.lower() in {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".php", ".java", ".go", ".jsp", ".jspf", ".xml", ".graphql", ".gql"}
    }
    known_modules = set(internal_files)

    for file_path, path in internal_files.items():
        text = read_text(path)
        python_analysis = analyze_python_file(path, source_root) if path.suffix.lower() == ".py" else None
        imports = parse_imports(path, text, source_root)
        for imported in imports[:32]:
            resolved_import = _resolve_internal_import(imported, known_modules)
            import_edges.append({"from": file_path, "to": resolved_import, "internal": resolved_import in known_modules})

        route_summary = detect_route_summary(path, text, source_root)
        if path.suffix.lower() == ".php" and route_summary is None and any(token in text.lower() for token in ("$_get", "$_post", "$_request", "session_start")):
            route_summary = {"file": file_path, "route_count": 1, "methods": ["GET", "POST"], "framework": "php"}
        if route_summary:
            route_nodes.append({"file": file_path, "route_count": route_summary["route_count"], "methods": route_summary["methods"]})

    call_edges = build_call_graph(source_root, list(internal_files.values()))
    for file_path, path in internal_files.items():
        if path.suffix.lower() == ".py":
            continue
        text = read_text(path)
        local_functions = _extract_local_functions(text)
        local_calls = _extract_call_targets(text)
        for function_name in local_functions[:32]:
            for target in local_calls[:48]:
                if target == function_name:
                    continue
                call_edges.append({"from": file_path, "function": function_name, "to": target, "line": 0})

    service_edges = build_service_graph(source_root, list(internal_files.values()))

    return {
        "primary_framework": framework_profile["primary_framework"],
        "import_edges": import_edges[:4000],
        "route_nodes": route_nodes[:80],
        "call_edges": call_edges[:4000],
        "service_edges": service_edges[:4000],
        "auth_nodes": auth_nodes[:80],
        "summary": {
            "import_edges": len(import_edges),
            "route_files": len(route_nodes),
            "call_edges": len(call_edges),
            "service_edges": len(service_edges),
            "auth_files": len(auth_nodes),
        },
    }


def _extract_local_functions(text: str) -> list[str]:
    return list(
        dict.fromkeys(
            re.findall(r"^\s*(?:async\s+def|def|function|const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.MULTILINE)
        )
    )


def _extract_call_targets(text: str) -> list[str]:
    ignored = {"if", "for", "while", "return", "print", "len", "range"}
    targets = [match.group(1) for match in CALL_PATTERN.finditer(text)]
    return [target for target in dict.fromkeys(targets) if target not in ignored]


def _resolve_internal_import(imported: str, known_modules: set[str]) -> str:
    if imported in known_modules:
        return imported

    python_candidate = f"{imported}.py"
    if python_candidate in known_modules:
        return python_candidate

    java_candidates = [
        f"{imported}.java",
        f"src/{imported}.java",
        f"{imported}/index.java",
    ]
    for candidate in java_candidates:
        if candidate in known_modules:
            return candidate

    js_candidates = [
        f"{imported}.ts",
        f"{imported}.tsx",
        f"{imported}.js",
        f"{imported}.jsx",
        f"{imported}/index.ts",
        f"{imported}/index.tsx",
        f"{imported}/index.js",
        f"{imported}/index.jsx",
    ]
    for candidate in js_candidates:
        if candidate in known_modules:
            return candidate

    php_candidates = [
        f"{imported}.php",
        f"{imported}.jsp",
        f"{imported}.jspf",
        f"{imported}/index.php",
    ]
    for candidate in php_candidates:
        if candidate in known_modules:
            return candidate

    go_candidates = [
        f"{imported}.go",
        f"src/{imported}.go",
        f"src/{imported}/main.go",
        f"src/{imported}/server.go",
    ]
    for candidate in go_candidates:
        if candidate in known_modules:
            return candidate
    return imported
