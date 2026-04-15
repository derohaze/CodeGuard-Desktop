import ast
from pathlib import Path

from app.infrastructure.services.repository.repository_analysis import read_text


def parse_file(path: Path) -> dict:
    text = read_text(path)
    language = detect_language(path)
    return {
        "path": str(path),
        "language": language,
        "text": text,
        "line_count": len(text.splitlines()),
    }


def parse_python_ast(path: Path) -> ast.AST | None:
    text = read_text(path)
    if not text.strip():
        return None
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def detect_language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".js", ".jsx", ".mjs", ".cjs"}:
        return "javascript"
    if suffix in {".ts", ".tsx"}:
        return "typescript"
    return suffix.lstrip(".") or "unknown"
