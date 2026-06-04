use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};
use std::time::Instant;

use crate::config::{IGNORED_DIRS, MAX_FILE_READ_BYTES, MAX_WALK_ENTRIES};
use crate::model::{HotspotFile, NativeIndex};

use super::hotspots::{push_bounded_hotspot, sort_hotspots};
use super::signals::{
    file_signals, hotspot_reasons, is_manifest, is_supported_scan_file, language_for_path, lower_file_name,
};

pub fn analyze_root(root: &Path, max_files: usize) -> Result<NativeIndex, String> {
    if max_files == 0 {
        return Err("--max-files must be greater than 0".to_string());
    }

    let started_at = Instant::now();
    let canonical_root = root.canonicalize().map_err(|error| format!("root is not readable: {error}"))?;
    let mut index = NativeIndex::default();
    let mut stack = vec![canonical_root.clone()];

    while let Some(directory) = stack.pop() {
        if index.stats.truncated {
            break;
        }
        index_directory(&canonical_root, directory, max_files, &mut stack, &mut index);
    }

    sort_hotspots(&mut index.hotspot_files);
    index.elapsed_ms = started_at.elapsed().as_millis();
    Ok(index)
}

fn index_directory(
    root: &Path,
    directory: PathBuf,
    max_files: usize,
    stack: &mut Vec<PathBuf>,
    index: &mut NativeIndex,
) {
    let entries = match fs::read_dir(&directory) {
        Ok(entries) => entries,
        Err(_) => {
            index.stats.unreadable_directories += 1;
            return;
        }
    };

    for entry_result in entries {
        index.stats.visited_entries += 1;
        if index.stats.visited_entries >= MAX_WALK_ENTRIES || index.files_indexed >= max_files {
            index.stats.truncated = true;
            return;
        }

        let entry = match entry_result {
            Ok(entry) => entry,
            Err(_) => {
                index.stats.skipped_files += 1;
                continue;
            }
        };
        let path = entry.path();
        let file_type = match entry.file_type() {
            Ok(file_type) => file_type,
            Err(_) => {
                index.stats.skipped_files += 1;
                continue;
            }
        };

        if file_type.is_symlink() {
            index.stats.skipped_files += 1;
            continue;
        }

        if file_type.is_dir() {
            let name = lower_file_name(&path);
            if IGNORED_DIRS.contains(&name.as_str()) {
                index.stats.skipped_directories += 1;
                continue;
            }
            stack.push(path);
            continue;
        }

        if !file_type.is_file() {
            index.stats.skipped_files += 1;
            continue;
        }

        if !is_supported_scan_file(&path) {
            index.stats.skipped_files += 1;
            continue;
        }

        index_file(root, &path, index);
    }
}

fn index_file(root: &Path, path: &Path, index: &mut NativeIndex) {
    index.files_indexed += 1;
    let relative = relative_path(root, path);

    if is_manifest(path) {
        index.manifests.insert(relative.clone());
    }

    let language = language_for_path(path);
    if !language.is_empty() {
        *index.languages.entry(language).or_insert(0) += 1;
    }

    let file_read = read_bounded_text(path);
    if file_read.unreadable {
        index.stats.unreadable_files += 1;
    }
    index.stats.bytes_read += file_read.bytes_read;
    if file_read.truncated {
        index.stats.oversized_files += 1;
    }

    let signals = file_signals(&relative, &file_read.text);
    if signals.route_hit {
        index.route_files += 1;
    }
    if signals.auth_hit {
        index.auth_files += 1;
    }
    index.source_markers += signals.source_hits;
    index.sink_markers += signals.sink_hits;

    let (score, reasons) = hotspot_reasons(&signals);
    if score > 0 {
        push_bounded_hotspot(index, HotspotFile { file: relative, score, reasons });
    }
}

fn read_bounded_text(path: &Path) -> FileRead {
    let mut file = match File::open(path) {
        Ok(file) => file,
        Err(_) => {
            return FileRead {
                unreadable: true,
                ..FileRead::default()
            };
        }
    };

    let capacity = fs::metadata(path)
        .map(|metadata| metadata.len().min(MAX_FILE_READ_BYTES) as usize)
        .unwrap_or(0);
    let mut buffer = Vec::with_capacity(capacity);

    if file.by_ref().take(MAX_FILE_READ_BYTES + 1).read_to_end(&mut buffer).is_err() {
        return FileRead {
            unreadable: true,
            ..FileRead::default()
        };
    }

    let truncated = buffer.len() as u64 > MAX_FILE_READ_BYTES;
    if truncated {
        buffer.truncate(MAX_FILE_READ_BYTES as usize);
    }

    FileRead {
        bytes_read: buffer.len(),
        text: String::from_utf8_lossy(&buffer).into_owned(),
        truncated,
        unreadable: false,
    }
}

fn relative_path(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .to_string_lossy()
        .replace('\\', "/")
}

#[derive(Default)]
struct FileRead {
    text: String,
    bytes_read: usize,
    truncated: bool,
    unreadable: bool,
}
