from pathlib import Path

from app.infrastructure.services.repository.repository_analysis import (
    MANIFEST_FILES,
    MAX_PROFILE_CONTENT_FILES,
    detect_framework_for_file,
    prioritize_files_for_analysis,
    read_text,
    relative_path,
)
from app.infrastructure.services.scan.score_calibration import build_support_matrix


def detect_framework_profile(source_root: Path, files: list[Path], repository_profile: dict) -> dict:
    framework_files: dict[str, list[str]] = {}
    manifest_signals: list[str] = []

    for path in prioritize_files_for_analysis(files, MAX_PROFILE_CONTENT_FILES):
        if path.name.lower() in MANIFEST_FILES:
            manifest_signals.append(relative_path(path, source_root))
            continue
        if path.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".php", ".java", ".go", ".xml", ".jsp", ".jspf", ".graphql", ".gql"}:
            continue
        framework = detect_framework_for_file(read_text(path))
        if framework == "unknown":
            continue
        framework_files.setdefault(framework, []).append(relative_path(path, source_root))

    ranked_frameworks = sorted(
        framework_files.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )
    discovered_frameworks = [name for name, _ in ranked_frameworks]
    if "graphql" in discovered_frameworks:
        primary_framework = "graphql"
    elif ranked_frameworks:
        primary_framework = ranked_frameworks[0][0]
    else:
        primary_framework = repository_profile["frameworks"][0] if repository_profile["frameworks"] else "unknown"

    profile = {
        "primary_framework": primary_framework,
        "frameworks": discovered_frameworks or repository_profile["frameworks"],
        "languages": repository_profile["languages"],
        "manifests": manifest_signals or repository_profile["manifests"],
        "framework_file_counts": {name: len(items) for name, items in ranked_frameworks},
        "entrypoints": repository_profile["entrypoints"],
    }
    profile["support_matrix"] = build_support_matrix(profile)
    return profile
