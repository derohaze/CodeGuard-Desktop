def prioritize_review_queue(work_items: list[dict], path_units: list[dict], scan_mode: str) -> dict:
    ranked_paths = sorted(
        path_units,
        key=lambda item: (
            -_path_priority_score(item),
            str(item.get("sink", {}).get("file", "")),
            int(item.get("sink", {}).get("line", 0)),
        ),
    )

    path_rank_lookup = {str(item.get("sink", {}).get("file", "")): index for index, item in enumerate(ranked_paths)}
    ranked_work_items = sorted(
        work_items,
        key=lambda item: (
            path_rank_lookup.get(str(item.get("file", "")), 999999),
            -int(item.get("signal_score", "1")),
            str(item.get("file", "")),
            int(item.get("start_line", "1")),
        ),
    )

    return {
        "review_items": ranked_work_items,
        "path_units": ranked_paths,
        "review_queue_summary": {
            "scan_mode": scan_mode,
            "ranked_review_items": len(ranked_work_items),
            "ranked_path_units": len(ranked_paths),
            "cross_file_paths": sum(1 for item in ranked_paths if item.get("path_type") == "cross_file"),
            "sanitized_paths": sum(1 for item in ranked_paths if item.get("has_sanitizer")),
        },
    }


def _path_priority_score(item: dict) -> int:
    score = int(item.get("confidence", 0))
    sink_kind = str(item.get("sink", {}).get("kind", ""))
    if sink_kind in {"command_execution", "unsafe_deserialization"}:
        score += 18
    elif sink_kind in {"outbound_request", "filesystem_access"}:
        score += 10
    if item.get("path_type") == "cross_file":
        score += 8
    if item.get("has_sanitizer"):
        score -= 24
    return score
