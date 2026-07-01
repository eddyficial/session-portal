"""Application logging setup.

Session Portal is a local desktop app, so failures need to be diagnosable
without a console window. This module creates one rotating log file beside the
v2 app data files and exposes named child loggers for providers, UI, and
storage modules.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import LOG_FILE

LOGGER_NAME = "session_portal"


def configure_logging() -> logging.Logger:
    """Configure and return the app logger.

    The guard keeps tests and repeated launches from attaching duplicate file
    handlers. A small rotating log gives bug reports useful context without
    allowing logs to grow forever.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


__all__ = ["configure_logging", "get_logger", "LOG_FILE"]
