from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class Color:
    RESET = "\033[0m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"


def enable_windows_ansi() -> None:
    if os.name == "nt":
        os.system("")  # noqa: S605,S607


LEVEL_COLORS = {
    logging.DEBUG: Color.DIM,
    logging.INFO: Color.GREEN,
    logging.WARNING: Color.YELLOW,
    logging.ERROR: Color.RED,
    logging.CRITICAL: Color.RED,
}


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = LEVEL_COLORS.get(record.levelno, Color.CYAN)
        created_at = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        component = "PYTHON" if record.name.startswith("commerceops.") else record.name.upper()
        if len(component) > 10:
            component = component[:10]
        request_id = getattr(record, "request_id", "-")
        message = record.getMessage()
        if record.exc_text:
            message = f"{message}\n{record.exc_text}"
        elif record.exc_info:
            import traceback
            message = f"{message}\n{''.join(traceback.format_exception(*record.exc_info))}"
        rid_part = "" if request_id == "-" else f" {Color.DIM}{request_id[:8]}{Color.RESET}"
        return (
            f"{Color.DIM}{created_at}{Color.RESET} "
            f"{color}[{component:<10}]{Color.RESET} "
            f"{message}{rid_part}"
        )


def configure_logging() -> None:
    enable_windows_ansi()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ConsoleFormatter())
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
