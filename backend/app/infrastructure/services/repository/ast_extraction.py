from pathlib import Path

from app.infrastructure.services.repository.file_parsing import parse_python_ast


def extract_ast(path: Path) -> dict:
    tree = parse_python_ast(path)
    return {
        "path": str(path),
        "language": "python" if path.suffix.lower() == ".py" else "unknown",
        "available": tree is not None,
        "node_count": sum(1 for _ in getattr(tree, "body", [])) if tree is not None else 0,
    }
