import asyncio
import multiprocessing
import os
import shutil
import subprocess
from multiprocessing.process import BaseProcess
from pathlib import Path

import uvicorn

from app.core.config import get_settings


BACKEND_ROOT = Path(__file__).resolve().parent
NODE_IO_ROOT = BACKEND_ROOT / "node"
RUST_INDEXER_ROOT = BACKEND_ROOT / "rust-indexer"
RUST_INDEXER_BINARY_NAME = "codeguard-rust-indexer.exe" if os.name == "nt" else "codeguard-rust-indexer"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
YELLOW = "\033[33m"

UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": f"%(levelprefix)s {CYAN}[python-api]{RESET} %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": f'%(levelprefix)s {CYAN}[python-api]{RESET} %(client_addr)s - "%(request_line)s" %(status_code)s',
            "use_colors": True,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}


def _run_embedded_worker() -> None:
    try:
        from arq import run_worker
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "QUEUE_BACKEND='arq' requires the optional queue dependencies. Install backend requirements in this Python environment."
        ) from exc

    from app.infrastructure.queue.arq_worker import WorkerSettings

    asyncio.set_event_loop(asyncio.new_event_loop())
    run_worker(WorkerSettings)


def _should_start_embedded_worker() -> bool:
    settings = get_settings()
    return settings.queue_backend == "arq" and settings.auto_start_queue_worker


def _should_enable_reload() -> bool:
    settings = get_settings()
    return (
        settings.api_reload_enabled
        and settings.app_env == "development"
        and settings.api_workers == 1
        and not _should_start_embedded_worker()
    )


def _reload_dirs() -> list[str]:
    return [str(BACKEND_ROOT / "app")]


def _start_embedded_worker() -> BaseProcess | None:
    if not _should_start_embedded_worker():
        return None
    context = multiprocessing.get_context("spawn")
    worker_process = context.Process(target=_run_embedded_worker, name="aegix-arq-worker", daemon=True)
    worker_process.start()
    return worker_process


def _stop_embedded_worker(worker_process: BaseProcess | None) -> None:
    if worker_process is None:
        return
    if worker_process.is_alive():
        worker_process.terminate()
        worker_process.join(timeout=5)
    if worker_process.is_alive():
        worker_process.kill()
        worker_process.join(timeout=5)


def _loopback_host(host: str) -> str:
    if host in {"0.0.0.0", "::", "[::]"}:
        return "127.0.0.1"
    return host


def _find_pnpm() -> str:
    executable = shutil.which("pnpm.cmd" if os.name == "nt" else "pnpm")
    if executable is None:
        raise RuntimeError("pnpm is required to run the backend Node I/O service.")
    return executable


def _ensure_node_io_dependencies(pnpm: str) -> None:
    if (NODE_IO_ROOT / "node_modules").exists():
        return
    subprocess.run([pnpm, "install"], cwd=NODE_IO_ROOT, check=True)


def _start_node_io() -> subprocess.Popen | None:
    settings = get_settings()
    try:
        pnpm = _find_pnpm()
        _ensure_node_io_dependencies(pnpm)
    except RuntimeError as exc:
        print(f"{GREEN}[backend-main]{RESET} {MAGENTA}node-io{RESET}=unavailable ({exc})", flush=True)
        return None

    env = os.environ.copy()
    env.setdefault("NODE_IO_HOST", settings.node_io_host)
    env.setdefault("NODE_IO_PORT", str(settings.node_io_port))
    return subprocess.Popen(
        [pnpm, "--silent", "io:dev"],
        cwd=NODE_IO_ROOT,
        env=env,
    )


def _stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _find_rust_indexer_binary() -> Path | None:
    settings = get_settings()
    candidates: list[Path] = []
    if settings.rust_indexer_binary:
        candidates.append(Path(settings.rust_indexer_binary).expanduser())
    candidates.extend(
        [
            RUST_INDEXER_ROOT / "target" / "release" / RUST_INDEXER_BINARY_NAME,
            RUST_INDEXER_ROOT / "target" / "debug" / RUST_INDEXER_BINARY_NAME,
        ]
    )
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved
    return None


def _maybe_build_rust_indexer() -> None:
    settings = get_settings()
    if not settings.rust_indexer_auto_build or _find_rust_indexer_binary() is not None:
        return

    cargo = shutil.which("cargo.exe" if os.name == "nt" else "cargo")
    if cargo is None:
        print(
            f"{GREEN}[backend-main]{RESET} {YELLOW}rust-indexer{RESET}=source-ready "
            "(cargo not found; skipping auto-build)",
            flush=True,
        )
        return
    subprocess.run([cargo, "build", "--release"], cwd=RUST_INDEXER_ROOT, check=True)


def _start_rust_indexer() -> subprocess.Popen | None:
    settings = get_settings()
    if not settings.rust_indexer_enabled:
        print(f"{GREEN}[backend-main]{RESET} {YELLOW}rust-indexer{RESET}=disabled", flush=True)
        return None

    try:
        _maybe_build_rust_indexer()
    except subprocess.CalledProcessError as exc:
        print(f"{GREEN}[backend-main]{RESET} {YELLOW}rust-indexer{RESET}=build-failed ({exc})", flush=True)
        return None

    binary = _find_rust_indexer_binary()
    if binary is None:
        print(
            f"{GREEN}[backend-main]{RESET} {YELLOW}rust-indexer{RESET}=source-ready "
            "(binary missing; run cargo build --release in backend/rust-indexer)",
            flush=True,
        )
        return None

    return subprocess.Popen(
        [
            str(binary),
            "serve",
            "--host",
            settings.rust_indexer_host,
            "--port",
            str(settings.rust_indexer_port),
        ],
        cwd=RUST_INDEXER_ROOT,
    )


if __name__ == "__main__":
    settings = get_settings()
    worker_process = _start_embedded_worker()
    node_process = _start_node_io()
    rust_process = _start_rust_indexer()
    reload_enabled = _should_enable_reload()
    rust_status = (
        f"{YELLOW}rust-indexer{RESET}=http://{settings.rust_indexer_host}:{settings.rust_indexer_port}"
        if rust_process is not None
        else f"{YELLOW}rust-indexer{RESET}=not-running (build required)"
    )
    try:
        print(
            f"{GREEN}[backend-main]{RESET} starting services | "
            f"{CYAN}python-api{RESET}=http://{_loopback_host(settings.app_host)}:{settings.app_port} | "
            f"{MAGENTA}node-io{RESET}=http://{settings.node_io_host}:{settings.node_io_port} | "
            f"{rust_status}",
            flush=True,
        )
        uvicorn.run(
            "app.main:app",
            host=settings.app_host,
            port=settings.app_port,
            workers=settings.api_workers,
            reload=reload_enabled,
            reload_dirs=_reload_dirs() if reload_enabled else None,
            log_config=UVICORN_LOG_CONFIG,
        )
    finally:
        _stop_process(node_process)
        _stop_process(rust_process)
        _stop_embedded_worker(worker_process)
