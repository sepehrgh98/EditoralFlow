"""Logging setup: one format for the whole app."""

import logging

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"

# Libraries that log routine steps at INFO; our own lines already cover them
QUIET_LOGGERS = ("httpx", "httpcore", "bm25s")


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger. Safe to call more than once (later calls replace handlers)."""
    logging.basicConfig(level=level.upper(), format=LOG_FORMAT, force=True)
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
