"""
Shared logging configuration.

Services should call `get_logger(__name__)` rather than configuring their
own handlers, so log format/level stays consistent across the app.
"""

import logging
import sys


_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger once, on app startup."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger. Safe to call before configure_logging."""
    return logging.getLogger(name)
