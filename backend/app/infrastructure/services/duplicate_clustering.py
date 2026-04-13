def cluster_findings(findings: list[dict]) -> list[dict]:
    clustered: list[dict] = []
    seen: set[tuple[str, int, int, str, str]] = set()
    for item in findings:
        key = (
            str(item.get("file", "")).strip(),
            int(item.get("line", 1)),
            int(item.get("line_end", item.get("line", 1))),
            str(item.get("title", "")).strip().lower(),
            str(item.get("path_hint", "")).strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        clustered.append(item)
    return clustered
