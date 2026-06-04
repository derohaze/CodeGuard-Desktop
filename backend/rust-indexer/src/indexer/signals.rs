use std::path::Path;

use crate::config::{AUTH_MARKERS, MANIFEST_FILES, ROUTE_MARKERS, SINK_MARKERS, SOURCE_MARKERS, SUPPORTED_EXTENSIONS};
use crate::model::FileSignals;

pub fn file_signals(relative_path: &str, content: &str) -> FileSignals {
    let lowered_path = relative_path.to_ascii_lowercase();
    let lowered_content = content.to_ascii_lowercase();
    FileSignals {
        route_hit: contains_any(&lowered_content, ROUTE_MARKERS),
        auth_hit: contains_any(&lowered_content, AUTH_MARKERS) || contains_any(&lowered_path, AUTH_MARKERS),
        source_hits: count_marker_hits(&lowered_content, SOURCE_MARKERS),
        sink_hits: count_marker_hits(&lowered_content, SINK_MARKERS),
    }
}

pub fn hotspot_reasons(signals: &FileSignals) -> (usize, Vec<&'static str>) {
    let mut score = 0;
    let mut reasons = Vec::new();
    if signals.route_hit {
        score += 6;
        reasons.push("request entrypoint");
    }
    if signals.auth_hit {
        score += 5;
        reasons.push("auth boundary");
    }
    if signals.source_hits > 0 {
        score += 3;
        reasons.push("untrusted input");
    }
    if signals.sink_hits > 0 {
        score += 4;
        reasons.push("sensitive sink");
    }
    (score, reasons)
}

pub fn is_supported_scan_file(path: &Path) -> bool {
    let file_name = lower_file_name(path);
    if MANIFEST_FILES.contains(&file_name.as_str()) {
        return true;
    }
    path.extension()
        .and_then(|value| value.to_str())
        .map(|ext| SUPPORTED_EXTENSIONS.contains(&ext.to_ascii_lowercase().as_str()))
        .unwrap_or(false)
}

pub fn is_manifest(path: &Path) -> bool {
    MANIFEST_FILES.contains(&lower_file_name(path).as_str())
}

pub fn language_for_path(path: &Path) -> String {
    match path.extension().and_then(|value| value.to_str()).unwrap_or_default().to_ascii_lowercase().as_str() {
        "py" => "python",
        "js" | "jsx" | "mjs" | "cjs" => "javascript",
        "ts" | "tsx" => "typescript",
        "java" | "jsp" | "jspf" | "xml" => "java",
        "go" => "go",
        "php" => "php",
        "rs" => "rust",
        "rb" => "ruby",
        "cs" => "csharp",
        "kt" => "kotlin",
        "graphql" | "gql" => "graphql",
        _ => "",
    }
    .to_string()
}

pub fn lower_file_name(path: &Path) -> String {
    path.file_name()
        .and_then(|value| value.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase()
}

fn contains_any(text: &str, markers: &[&str]) -> bool {
    markers.iter().any(|marker| text.contains(marker))
}

fn count_marker_hits(text: &str, markers: &[&str]) -> usize {
    markers.iter().filter(|marker| text.contains(**marker)).count()
}
