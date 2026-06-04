from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

from app.core.config import get_settings


BACKEND_ROOT = Path(__file__).resolve().parents[4]
RUST_INDEXER_ROOT = BACKEND_ROOT / "rust-indexer"
DEFAULT_BINARY_NAME = "codeguard-rust-indexer.exe" if os.name == "nt" else "codeguard-rust-indexer"
logger = logging.getLogger("aegix.rust-indexer")


def build_native_index(source_root: Path) -> dict:
    settings = get_settings()
    source_root = source_root.expanduser().resolve()
    if not settings.rust_indexer_enabled:
        return _unavailable("disabled", log=True)

    binary = _resolve_indexer_binary(settings.rust_indexer_binary)
    if binary is None:
        return _unavailable("binary_missing", log=True)

    timeout_seconds = max(1.0, float(settings.rust_indexer_analyze_timeout_seconds))
    logger.info(
        "[rust-indexer] analyze start | max_files=%s timeout_seconds=%.1f",
        settings.rust_indexer_max_files,
        timeout_seconds,
    )
    try:
        completed = subprocess.run(
            [
                str(binary),
                "analyze",
                "--root",
                str(source_root),
                "--max-files",
                str(settings.rust_indexer_max_files),
            ],
            cwd=RUST_INDEXER_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return _unavailable("timeout", log=True)
    except OSError:
        return _unavailable("launch_failed", log=True)

    if completed.returncode != 0:
        return _unavailable("runtime_failed", log=True)

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return _unavailable("invalid_output", log=True)

    if not isinstance(payload, dict):
        return _unavailable("invalid_output", log=True)

    logger.info(
        "[rust-indexer] analyze ok | files_indexed=%s elapsed_ms=%s route_files=%s auth_files=%s hotspots=%s",
        int(payload.get("files_indexed", 0) or 0),
        int(payload.get("elapsed_ms", 0) or 0),
        int(payload.get("route_files", 0) or 0),
        int(payload.get("auth_files", 0) or 0),
        len(payload.get("hotspot_files", []) if isinstance(payload.get("hotspot_files", []), list) else []),
    )

    return {
        "available": True,
        "engine": "rust-indexer",
        "schema_version": int(payload.get("schema_version", 1) or 1),
        "files_indexed": int(payload.get("files_indexed", 0) or 0),
        "languages": payload.get("languages", {}),
        "manifests": payload.get("manifests", []),
        "route_files": int(payload.get("route_files", 0) or 0),
        "auth_files": int(payload.get("auth_files", 0) or 0),
        "source_markers": int(payload.get("source_markers", 0) or 0),
        "sink_markers": int(payload.get("sink_markers", 0) or 0),
        "hotspot_files": payload.get("hotspot_files", [])[:24],
        "stats": payload.get("stats", {}),
        "elapsed_ms": int(payload.get("elapsed_ms", 0) or 0),
    }


def _resolve_indexer_binary(configured_binary: str | None) -> Path | None:
    candidates: list[Path] = []
    if configured_binary:
        candidates.append(Path(configured_binary).expanduser())
    candidates.extend(
        [
            RUST_INDEXER_ROOT / "target" / "release" / DEFAULT_BINARY_NAME,
            RUST_INDEXER_ROOT / "target" / "debug" / DEFAULT_BINARY_NAME,
        ]
    )

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved
    return None


def _unavailable(reason: str, *, log: bool = False) -> dict:
    if log:
        logger.info("[rust-indexer] analyze unavailable | reason=%s", reason)
    return {
        "available": False,
        "engine": "rust-indexer",
        "reason": reason,
    }
