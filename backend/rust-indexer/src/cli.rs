use std::path::PathBuf;

use crate::config::{DEFAULT_HOST, DEFAULT_MAX_FILES, DEFAULT_PORT, MAX_FILES_LIMIT};
use crate::model::{AnalyzeConfig, ServerConfig};

pub enum Command {
    Analyze(AnalyzeConfig),
    Serve(ServerConfig),
}

pub fn parse_command<I>(args: I) -> Result<Command, String>
where
    I: IntoIterator<Item = String>,
{
    let args: Vec<String> = args.into_iter().collect();
    match args.first().map(String::as_str) {
        Some("analyze") => parse_analyze(&args[1..]),
        Some("serve") => parse_serve(&args[1..]),
        _ => Err("unknown command".to_string()),
    }
}

pub fn print_usage() {
    eprintln!("{}[rust-indexer]{} usage:", crate::log::YELLOW, crate::log::RESET);
    eprintln!("  codeguard-rust-indexer serve --host 127.0.0.1 --port 7100");
    eprintln!("  codeguard-rust-indexer analyze --root <path> [--max-files 12000]");
}

fn parse_analyze(args: &[String]) -> Result<Command, String> {
    let root = string_flag(args, "--root").ok_or_else(|| "--root is required".to_string())?;
    let max_files = number_flag(args, "--max-files").unwrap_or(DEFAULT_MAX_FILES);
    if max_files == 0 || max_files > MAX_FILES_LIMIT {
        return Err(format!("--max-files must be between 1 and {MAX_FILES_LIMIT}"));
    }
    Ok(Command::Analyze(AnalyzeConfig {
        root: PathBuf::from(root),
        max_files,
    }))
}

fn parse_serve(args: &[String]) -> Result<Command, String> {
    let host = string_flag(args, "--host").unwrap_or_else(|| DEFAULT_HOST.to_string());
    let port = number_flag(args, "--port").unwrap_or(DEFAULT_PORT as usize);
    if port == 0 || port > u16::MAX as usize {
        return Err("--port must be between 1 and 65535".to_string());
    }
    Ok(Command::Serve(ServerConfig {
        host,
        port: port as u16,
    }))
}

fn string_flag(args: &[String], name: &str) -> Option<String> {
    args.windows(2)
        .find(|window| window[0] == name)
        .map(|window| window[1].clone())
}

fn number_flag(args: &[String], name: &str) -> Option<usize> {
    string_flag(args, name).and_then(|value| value.parse::<usize>().ok())
}
