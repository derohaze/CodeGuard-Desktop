mod cli;
mod config;
mod http;
mod indexer;
mod json;
mod log;
mod model;

use cli::{parse_command, print_usage, Command};

fn main() {
    let result = match parse_command(std::env::args().skip(1)) {
        Ok(Command::Analyze(config)) => indexer::analyze_root(&config.root, config.max_files)
            .map(|index| println!("{}", json::index_to_json(&index))),
        Ok(Command::Serve(config)) => http::serve(config),
        Err(error) => {
            print_usage();
            Err(error)
        }
    };

    if let Err(error) = result {
        log::error(&error);
        std::process::exit(1);
    }
}
