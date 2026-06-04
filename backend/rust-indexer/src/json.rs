use crate::model::{HotspotFile, NativeIndex};

pub fn index_to_json(index: &NativeIndex) -> String {
    let languages = index
        .languages
        .iter()
        .map(|(language, count)| format!(r#""{}":{}"#, json_escape(language), count))
        .collect::<Vec<_>>()
        .join(",");
    let manifests = index
        .manifests
        .iter()
        .map(|item| format!(r#""{}""#, json_escape(item)))
        .collect::<Vec<_>>()
        .join(",");
    let hotspots = index
        .hotspot_files
        .iter()
        .map(hotspot_to_json)
        .collect::<Vec<_>>()
        .join(",");

    format!(
        r#"{{"engine":"rust-indexer","schema_version":1,"files_indexed":{},"languages":{{{}}},"manifests":[{}],"route_files":{},"auth_files":{},"source_markers":{},"sink_markers":{},"hotspot_files":[{}],"stats":{{"visited_entries":{},"skipped_directories":{},"skipped_files":{},"unreadable_directories":{},"unreadable_files":{},"bytes_read":{},"oversized_files":{},"truncated":{}}},"elapsed_ms":{}}}"#,
        index.files_indexed,
        languages,
        manifests,
        index.route_files,
        index.auth_files,
        index.source_markers,
        index.sink_markers,
        hotspots,
        index.stats.visited_entries,
        index.stats.skipped_directories,
        index.stats.skipped_files,
        index.stats.unreadable_directories,
        index.stats.unreadable_files,
        index.stats.bytes_read,
        index.stats.oversized_files,
        if index.stats.truncated { "true" } else { "false" },
        index.elapsed_ms
    )
}

fn hotspot_to_json(item: &HotspotFile) -> String {
    let reasons = item
        .reasons
        .iter()
        .map(|reason| format!(r#""{}""#, json_escape(reason)))
        .collect::<Vec<_>>()
        .join(",");
    format!(
        r#"{{"file":"{}","score":{},"reasons":[{}]}}"#,
        json_escape(&item.file),
        item.score,
        reasons
    )
}

pub fn json_escape(value: &str) -> String {
    let mut escaped = String::with_capacity(value.len());
    for ch in value.chars() {
        match ch {
            '"' => escaped.push_str("\\\""),
            '\\' => escaped.push_str("\\\\"),
            '\n' => escaped.push_str("\\n"),
            '\r' => escaped.push_str("\\r"),
            '\t' => escaped.push_str("\\t"),
            other if other.is_control() => escaped.push_str(&format!("\\u{:04x}", other as u32)),
            other => escaped.push(other),
        }
    }
    escaped
}
