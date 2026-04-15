from difflib import unified_diff


def render_unified_diff(file_path: str, before_snippet: str, after_snippet: str) -> str:
    if not before_snippet and not after_snippet:
        return ""
    lines = unified_diff(
        before_snippet.splitlines(),
        after_snippet.splitlines(),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm="",
    )
    return "\n".join(lines)
