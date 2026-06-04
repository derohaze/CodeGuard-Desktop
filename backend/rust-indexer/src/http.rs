use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};

use crate::log;
use crate::model::ServerConfig;

pub fn serve(config: ServerConfig) -> Result<(), String> {
    let listener = TcpListener::bind(format!("{}:{}", config.host, config.port))
        .map_err(|error| format!("bind failed: {error}"))?;
    log::startup(&format!("listening on http://{}:{}", config.host, config.port));

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                if let Err(error) = handle_connection(stream) {
                    log::request_error(&error);
                }
            }
            Err(error) => log::request_error(&format!("accept error: {error}")),
        }
    }
    Ok(())
}

fn handle_connection(mut stream: TcpStream) -> Result<(), String> {
    let mut buffer = [0_u8; 2048];
    let size = stream.read(&mut buffer).map_err(|error| error.to_string())?;
    let request = String::from_utf8_lossy(&buffer[..size]);
    let request_line = request.lines().next().unwrap_or_default();
    let parts: Vec<&str> = request_line.split_whitespace().collect();
    let method = parts.get(0).copied().unwrap_or("GET");
    let path = parts.get(1).copied().unwrap_or("/");

    if method == "GET" && (path == "/health" || path == "/api/v1/rust/health") {
        write_json(
            &mut stream,
            200,
            r#"{"status":"ok","service":"rust-indexer","role":"native-code-index","owned_surfaces":["local-static-analysis","bounded-file-indexing"]}"#,
        )?;
        log::request(method, path, 200);
        return Ok(());
    }

    write_json(&mut stream, 404, r#"{"detail":"Route not found."}"#)?;
    log::request(method, path, 404);
    Ok(())
}

fn write_json(stream: &mut TcpStream, status_code: u16, body: &str) -> Result<(), String> {
    let status_text = match status_code {
        200 => "OK",
        404 => "Not Found",
        _ => "OK",
    };
    let response = format!(
        "HTTP/1.1 {status_code} {status_text}\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
        body.as_bytes().len()
    );
    stream.write_all(response.as_bytes()).map_err(|error| error.to_string())
}
