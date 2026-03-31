"""Tests for kubeidea.utils.logging module."""

import logging

from kubeidea.utils.logging import setup_logging


def test_setup_logging_returns_logger() -> None:
    """setup_logging should return a configured logger."""
    logger = setup_logging(level=logging.DEBUG)
    assert logger.name == "kubeidea"
    assert logger.level == logging.DEBUG


def test_setup_logging_idempotent() -> None:
    """Calling setup_logging twice should not duplicate handlers."""
    logger1 = setup_logging()
    handler_count = len(logger1.handlers)
    logger2 = setup_logging()
    assert len(logger2.handlers) == handler_count
