pub const RESET: &str = "\x1b[0m";
pub const YELLOW: &str = "\x1b[33m";
pub const GREEN: &str = "\x1b[32m";
pub const RED: &str = "\x1b[31m";

pub fn startup(message: &str) {
    eprintln!("{YELLOW}[rust-indexer]{RESET} {message}");
}

pub fn request(method: &str, path: &str, status_code: u16) {
    let color = if status_code >= 500 {
        RED
    } else if status_code >= 400 {
        YELLOW
    } else {
        GREEN
    };
    eprintln!("{YELLOW}[rust-indexer]{RESET} {method:<6} {path} {color}{status_code}{RESET}");
}

pub fn request_error(error: &str) {
    eprintln!("{YELLOW}[rust-indexer]{RESET} {RED}request error{RESET} {error}");
}

pub fn error(error: &str) {
    eprintln!("{YELLOW}[rust-indexer]{RESET} {RED}error{RESET} {error}");
}
