import ast
from pathlib import Path

from app.infrastructure.services.repository.repository_analysis import read_text, relative_path


SOURCE_CALLS = {
    "json": "http_input",
    "body": "http_input",
    "form": "http_input",
    "query_params": "http_input",
    "request.json": "http_input",
    "request.body": "http_input",
    "request.form": "http_input",
    "req.body": "http_input",
    "req.query": "http_input",
    "req.params": "http_input",
}
SINK_CALLS = {
    "os.system": "command_execution",
    "subprocess.run": "command_execution",
    "subprocess.Popen": "command_execution",
    "subprocess.call": "command_execution",
    "requests.get": "outbound_request",
    "requests.post": "outbound_request",
    "httpx.get": "outbound_request",
    "httpx.post": "outbound_request",
    "open": "filesystem_access",
    "pickle.load": "unsafe_deserialization",
    "pickle.loads": "unsafe_deserialization",
    "yaml.load": "unsafe_deserialization",
}
SANITIZER_CALLS = {
    "sanitize": "input_validation",
    "validate": "input_validation",
    "escape": "input_validation",
    "os.path.normpath": "path_normalization",
    "Path.resolve": "path_normalization",
}


def analyze_python_file(path: Path, source_root: Path) -> dict:
    text = read_text(path)
    if not text.strip():
        return empty_python_analysis(relative_path(path, source_root))

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return empty_python_analysis(relative_path(path, source_root))

    visitor = PythonFlowVisitor(relative_path(path, source_root))
    visitor.visit(tree)
    return visitor.to_artifact()


def empty_python_analysis(file_path: str) -> dict:
    return {
        "file": file_path,
        "functions": [],
        "calls": [],
        "assignments": [],
        "returns": [],
        "sources": [],
        "sinks": [],
        "sanitizers": [],
        "imports": {},
    }


class PythonFlowVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.current_function = "module"
        self.functions: list[dict] = []
        self.calls: list[dict] = []
        self.assignments: list[dict] = []
        self.returns: list[dict] = []
        self.sources: list[dict] = []
        self.sinks: list[dict] = []
        self.sanitizers: list[dict] = []
        self.imports: dict[str, str] = {}

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            qualified = f"{module}.{alias.name}".strip(".")
            self.imports[alias.asname or alias.name] = qualified
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous = self.current_function
        self.current_function = node.name
        self.functions.append(
            {
                "name": node.name,
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
                "params": [arg.arg for arg in node.args.args],
            }
        )
        self.generic_visit(node)
        self.current_function = previous

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        value_symbols = extract_symbols(node.value)
        value_call = resolve_call_name(node.value, self.imports)
        for target in node.targets:
            for name in extract_target_names(target):
                self.assignments.append(
                    {
                        "function": self.current_function,
                        "target": name,
                        "value_symbols": value_symbols,
                        "value_call": value_call,
                        "line": node.lineno,
                    }
                )
                if value_call in SOURCE_CALLS:
                    self.sources.append(
                        {
                            "file": self.file_path,
                            "line": node.lineno,
                            "kind": SOURCE_CALLS[value_call],
                            "label": value_call,
                            "function": self.current_function,
                            "symbol": name,
                        }
                    )
                if value_call in SANITIZER_CALLS:
                    self.sanitizers.append(
                        {
                            "file": self.file_path,
                            "line": node.lineno,
                            "kind": SANITIZER_CALLS[value_call],
                            "label": value_call,
                            "function": self.current_function,
                            "symbol": name,
                            "input_symbols": value_symbols,
                        }
                    )
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        self.returns.append(
            {
                "function": self.current_function,
                "line": node.lineno,
                "symbols": extract_symbols(node.value) if node.value else [],
            }
        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        qualified_name = resolve_call_name(node, self.imports)
        arg_symbols = []
        for arg in node.args:
            arg_symbols.extend(extract_symbols(arg))

        call_record = {
            "file": self.file_path,
            "function": self.current_function,
            "line": node.lineno,
            "call": qualified_name,
            "arg_symbols": list(dict.fromkeys(arg_symbols)),
        }
        self.calls.append(call_record)

        if qualified_name in SOURCE_CALLS:
            self.sources.append(
                {
                    "file": self.file_path,
                    "line": node.lineno,
                    "kind": SOURCE_CALLS[qualified_name],
                    "label": qualified_name,
                    "function": self.current_function,
                    "symbol": qualified_name,
                }
            )
        if qualified_name in SINK_CALLS:
            self.sinks.append(
                {
                    "file": self.file_path,
                    "line": node.lineno,
                    "kind": SINK_CALLS[qualified_name],
                    "label": qualified_name,
                    "function": self.current_function,
                    "symbols": list(dict.fromkeys(arg_symbols)),
                }
            )
        if qualified_name in SANITIZER_CALLS:
            self.sanitizers.append(
                {
                    "file": self.file_path,
                    "line": node.lineno,
                    "kind": SANITIZER_CALLS[qualified_name],
                    "label": qualified_name,
                    "function": self.current_function,
                    "symbol": qualified_name,
                    "input_symbols": list(dict.fromkeys(arg_symbols)),
                }
            )
        self.generic_visit(node)

    def to_artifact(self) -> dict:
        return {
            "file": self.file_path,
            "functions": self.functions,
            "calls": self.calls,
            "assignments": self.assignments,
            "returns": self.returns,
            "sources": self.sources,
            "sinks": self.sinks,
            "sanitizers": self.sanitizers,
            "imports": self.imports,
        }


def resolve_call_name(node: ast.AST | None, imports: dict[str, str]) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Call):
        return resolve_call_name(node.func, imports)
    if isinstance(node, ast.Name):
        return imports.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = resolve_call_name(node.value, imports)
        return f"{base}.{node.attr}".strip(".")
    return ""


def extract_symbols(node: ast.AST | None) -> list[str]:
    if node is None:
        return []
    symbols: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            symbols.append(child.id)
        elif isinstance(child, ast.Attribute):
            symbols.append(child.attr)
    return list(dict.fromkeys(symbols))


def extract_target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        names: list[str] = []
        for item in node.elts:
            names.extend(extract_target_names(item))
        return names
    return []
