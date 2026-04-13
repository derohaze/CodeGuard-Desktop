from pathlib import Path

from app.infrastructure.services.repository_analysis import read_text


def trace_candidate_paths(
    source_root: Path,
    repository_graph: dict,
    registry: dict,
    files: list[Path],
) -> dict:
    file_lookup = {path.relative_to(source_root).as_posix(): path for path in files if path.is_file()}
    imports_by_file: dict[str, list[str]] = {}
    for edge in repository_graph.get("import_edges", []):
        imports_by_file.setdefault(edge["from"], []).append(edge["to"])
    for edge in repository_graph.get("service_edges", []):
        imports_by_file.setdefault(edge["from"], []).append(edge["to"])

    python_analyses = registry.get("python_analyses", {})
    sources_by_file = _group_by_file(registry.get("sources", []))
    sanitizers_by_file = _group_by_file(registry.get("sanitizers", []))
    candidate_paths = _trace_python_paths(python_analyses, imports_by_file)

    for sink in registry.get("sinks", []):
        sink_file = sink["file"]
        existing = any(item["sink"]["file"] == sink_file and item["sink"]["line"] == sink["line"] for item in candidate_paths)
        if existing:
            continue

        direct_sources = sources_by_file.get(sink_file, [])
        if direct_sources:
            for source in direct_sources[:2]:
                candidate_paths.append(
                    _make_path(
                        source=source,
                        sink=sink,
                        nodes=[sink_file],
                        sanitizer=_registry_path_has_sanitizer(source, sink, sanitizers_by_file.get(sink_file, [])),
                        path_type="intra_file",
                        line_sequence=[int(source["line"]), int(sink["line"])],
                    )
                )
            continue

        inbound_chains = _find_inbound_source_chains(imports_by_file, sink_file, max_depth=5)
        for chain in inbound_chains[:6]:
            inbound_file = chain[0]
            for source in sources_by_file.get(inbound_file, [])[:2]:
                candidate_paths.append(
                    _make_path(
                        source=source,
                        sink=sink,
                        nodes=chain,
                        sanitizer=False,
                        path_type="cross_file",
                        line_sequence=[int(source["line"]), int(sink["line"])],
                    )
                )

    enriched_paths: list[dict] = []
    for item in candidate_paths:
        source_path = file_lookup.get(item["source"]["file"])
        sink_path = file_lookup.get(item["sink"]["file"])
        evidence_lines = []
        if source_path is not None:
            evidence_lines.append({"file": item["source"]["file"], "line": int(item["source"]["line"]), "code": _extract_line(source_path, int(item["source"]["line"]))})
        if sink_path is not None:
            evidence_lines.append({"file": item["sink"]["file"], "line": int(item["sink"]["line"]), "code": _extract_line(sink_path, int(item["sink"]["line"]))})
        item["path_hint"] = " -> ".join(item["nodes"])
        item["evidence"] = "\n".join(
            f"{entry['file']}:{entry['line']} {entry['code']}"
            for entry in evidence_lines
            if entry["code"]
        )
        item["evidence_lines"] = evidence_lines
        item["confidence"] = _score_path(item)
        enriched_paths.append(item)

    enriched_paths.sort(key=lambda item: (-item["confidence"], item["sink"]["file"], item["sink"]["line"]))
    return {
        "paths": enriched_paths[:40],
        "summary": {
            "candidate_path_count": len(enriched_paths),
            "intra_file_paths": sum(1 for item in enriched_paths if item["path_type"] == "intra_file"),
            "cross_file_paths": sum(1 for item in enriched_paths if item["path_type"] == "cross_file"),
            "sanitized_paths": sum(1 for item in enriched_paths if item["has_sanitizer"]),
            "path_evidence_present": len(enriched_paths) > 0,
        },
    }


def _trace_python_paths(python_analyses: dict[str, dict], imports_by_file: dict[str, list[str]]) -> list[dict]:
    paths: list[dict] = []
    for file_path, analysis in python_analyses.items():
        sources_by_function = _group_by_key(analysis.get("sources", []), "function")
        sanitizers_by_function = _group_by_key(analysis.get("sanitizers", []), "function")
        assignments_by_function = _group_by_key(analysis.get("assignments", []), "function")
        calls_by_function = _group_by_key(analysis.get("calls", []), "function")

        for sink in analysis.get("sinks", []):
            function_name = sink.get("function", "module")
            source = _find_local_source(
                sink_symbols=sink.get("symbols", []),
                sources=sources_by_function.get(function_name, []),
                assignments=assignments_by_function.get(function_name, []),
                sanitizers=sanitizers_by_function.get(function_name, []),
            )
            if source:
                sanitizer = _path_has_sanitizer(sink.get("symbols", []), sanitizers_by_function.get(function_name, []), assignments_by_function.get(function_name, []))
                paths.append(
                    _make_path(
                        source=source,
                        sink=sink,
                        nodes=[file_path],
                        sanitizer=sanitizer,
                        path_type="intra_file",
                        line_sequence=[int(source["line"]), int(sink["line"])],
                    )
                )
                continue

            call_source = _find_call_source(
                sink=sink,
                current_file=file_path,
                current_function=function_name,
                imports_by_file=imports_by_file,
                python_analyses=python_analyses,
                calls=calls_by_function.get(function_name, []),
            )
            if call_source:
                paths.append(call_source)
    return paths


def _find_local_source(sink_symbols: list[str], sources: list[dict], assignments: list[dict], sanitizers: list[dict]) -> dict | None:
    source_symbols = {item.get("symbol") for item in sources if item.get("symbol")}
    tainted = set(source_symbols)
    changed = True
    while changed:
        changed = False
        for assignment in assignments:
            target = assignment.get("target")
            if not target or target in tainted:
                continue
            value_symbols = set(assignment.get("value_symbols", []))
            if tainted & value_symbols:
                tainted.add(target)
                changed = True

    for sanitizer in sanitizers:
        symbol = sanitizer.get("symbol")
        if symbol in tainted:
            tainted.discard(symbol)

    for source in sources:
        if source.get("symbol") in sink_symbols or any(symbol in tainted for symbol in sink_symbols):
            return source
    return None


def _path_has_sanitizer(sink_symbols: list[str], sanitizers: list[dict], assignments: list[dict]) -> bool:
    sanitized = {item.get("symbol") for item in sanitizers if item.get("symbol")}
    if sanitized & set(sink_symbols):
        return True
    for assignment in assignments:
        if assignment.get("target") in sink_symbols and assignment.get("value_call"):
            if assignment["value_call"] in {"sanitize", "validate", "escape", "os.path.normpath", "Path.resolve"}:
                return True
    return False


def _find_call_source(
    sink: dict,
    current_file: str,
    current_function: str,
    imports_by_file: dict[str, list[str]],
    python_analyses: dict[str, dict],
    calls: list[dict],
) -> dict | None:
    inbound_files = [file_path for file_path, imports in imports_by_file.items() if current_file in imports]
    for inbound_file in inbound_files:
        analysis = python_analyses.get(inbound_file)
        if analysis is None:
            continue
        local_sources = analysis.get("sources", [])
        for call in analysis.get("calls", []):
            if current_function not in call.get("call", ""):
                continue
            source = _find_local_source(
                sink_symbols=call.get("arg_symbols", []),
                sources=[item for item in local_sources if item.get("function") == call.get("function")],
                assignments=[item for item in analysis.get("assignments", []) if item.get("function") == call.get("function")],
                sanitizers=[item for item in analysis.get("sanitizers", []) if item.get("function") == call.get("function")],
            )
            if source:
                sanitizer = _path_has_sanitizer(
                    call.get("arg_symbols", []),
                    [item for item in analysis.get("sanitizers", []) if item.get("function") == call.get("function")],
                    [item for item in analysis.get("assignments", []) if item.get("function") == call.get("function")],
                )
                return _make_path(
                    source=source,
                    sink=sink,
                    nodes=[inbound_file, current_file],
                    sanitizer=sanitizer,
                    path_type="cross_file",
                    line_sequence=[int(source["line"]), int(call["line"]), int(sink["line"])],
                )
    return None


def _group_by_file(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(item["file"], []).append(item)
    return grouped


def _group_by_key(items: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(str(item.get(key, "module")), []).append(item)
    return grouped


def _make_path(source: dict, sink: dict, nodes: list[str], sanitizer: bool, path_type: str, line_sequence: list[int]) -> dict:
    return {
        "source": source,
        "sink": sink,
        "nodes": nodes,
        "path_type": path_type,
        "has_sanitizer": sanitizer,
        "line_sequence": sorted(set(line_sequence)),
    }


def _score_path(item: dict) -> int:
    base = 80 if item["path_type"] == "intra_file" else 86
    if item["has_sanitizer"]:
        base -= 28
    base += min(6, max(0, len(item.get("line_sequence", [])) - 2) * 2)
    return max(25, min(97, base))


def _extract_line(path: Path, line_number: int) -> str:
    lines = read_text(path).splitlines()
    if not lines:
        return ""
    index = max(0, min(len(lines) - 1, line_number - 1))
    return lines[index].strip()


def _registry_path_has_sanitizer(source: dict, sink: dict, sanitizers: list[dict]) -> bool:
    source_line = int(source.get("line", 0) or 0)
    sink_line = int(sink.get("line", 0) or 0)
    if source_line <= 0 or sink_line <= 0:
        return False
    lower = min(source_line, sink_line)
    upper = max(source_line, sink_line)
    return any(lower <= int(item.get("line", 0) or 0) <= upper for item in sanitizers)


def _find_inbound_source_chains(imports_by_file: dict[str, list[str]], sink_file: str, max_depth: int = 3) -> list[list[str]]:
    chains: list[list[str]] = []
    queue: list[list[str]] = [[sink_file]]
    visited: set[tuple[str, ...]] = set()

    while queue:
        chain = queue.pop(0)
        current = chain[0]
        predecessors = [
            file_path
            for file_path, imports in imports_by_file.items()
            if current in imports and file_path not in chain
        ]
        if not predecessors or len(chain) >= max_depth:
            if len(chain) > 1:
                chains.append(chain)
            continue
        for predecessor in predecessors:
            next_chain = [predecessor, *chain]
            key = tuple(next_chain)
            if key in visited:
                continue
            visited.add(key)
            queue.append(next_chain)
    return chains
