use std::collections::{BTreeMap, BTreeSet};
use std::path::PathBuf;

#[derive(Debug)]
pub struct AnalyzeConfig {
    pub root: PathBuf,
    pub max_files: usize,
}

#[derive(Debug)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
}

#[derive(Default)]
pub struct IndexStats {
    pub visited_entries: usize,
    pub skipped_directories: usize,
    pub skipped_files: usize,
    pub unreadable_directories: usize,
    pub unreadable_files: usize,
    pub bytes_read: usize,
    pub oversized_files: usize,
    pub truncated: bool,
}

#[derive(Default)]
pub struct NativeIndex {
    pub files_indexed: usize,
    pub languages: BTreeMap<String, usize>,
    pub manifests: BTreeSet<String>,
    pub route_files: usize,
    pub auth_files: usize,
    pub source_markers: usize,
    pub sink_markers: usize,
    pub hotspot_files: Vec<HotspotFile>,
    pub stats: IndexStats,
    pub elapsed_ms: u128,
}

#[derive(Clone)]
pub struct HotspotFile {
    pub file: String,
    pub score: usize,
    pub reasons: Vec<&'static str>,
}

pub struct FileSignals {
    pub route_hit: bool,
    pub auth_hit: bool,
    pub source_hits: usize,
    pub sink_hits: usize,
}
