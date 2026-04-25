from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.INFO)
    root.addHandler(file_handler)

    # User-facing console must stay readable. Raw subprocess/debug logs are noisy
    # during strategy tests, so by default they go only to the log file. Set
    # DEDZAPRET_CONSOLE_LOGS=1 to mirror INFO logs to console while debugging.
    if os.environ.get("DEDZAPRET_CONSOLE_LOGS") == "1":
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(fmt)
        stream_handler.setLevel(logging.INFO)
        root.addHandler(stream_handler)
