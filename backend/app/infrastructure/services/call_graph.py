from pathlib import Path

from app.infrastructure.services.python_flow_analysis import analyze_python_file


def build_call_graph(source_root: Path, files: list[Path]) -> list[dict]:
    edges: list[dict] = []
    for path in files:
        if path.suffix.lower() != ".py":
            continue
        analysis = analyze_python_file(path, source_root)
        for call in analysis.get("calls", []):
            edges.append(
                {
                    "from": analysis["file"],
                    "function": call.get("function", "module"),
                    "to": call.get("call", ""),
                    "line": int(call.get("line", 0)),
                }
            )
    return edges
