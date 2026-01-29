"""
Tests for gaugid.logger module.

Tests logging configuration and logger creation.
"""

import logging
import sys
from io import StringIO
from gaugid.logger import get_logger, setup_logging, LOGGER_NAME, DEFAULT_LOG_LEVEL


def test_get_logger_default() -> None:
    """Test getting default logger."""
    logger = get_logger()
    assert logger.name == LOGGER_NAME
    assert isinstance(logger, logging.Logger)


def test_get_logger_with_name() -> None:
    """Test getting logger with custom name."""
    logger = get_logger("test_module")
    assert logger.name == f"{LOGGER_NAME}.test_module"
    assert isinstance(logger, logging.Logger)


def test_get_logger_different_names() -> None:
    """Test getting different loggers."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    
    assert logger1.name == f"{LOGGER_NAME}.module1"
    assert logger2.name == f"{LOGGER_NAME}.module2"
    assert logger1 is not logger2


def test_setup_logging_default() -> None:
    """Test setting up logging with default configuration."""
    setup_logging()
    
    logger = logging.getLogger(LOGGER_NAME)
    assert logger.level == DEFAULT_LOG_LEVEL
    assert len(logger.handlers) > 0
    assert not logger.propagate


def test_setup_logging_custom_level() -> None:
    """Test setting up logging with custom level."""
    setup_logging(level=logging.DEBUG)
    
    logger = logging.getLogger(LOGGER_NAME)
    assert logger.level == logging.DEBUG


def test_setup_logging_custom_format() -> None:
    """Test setting up logging with custom format."""
    format_string = "%(levelname)s - %(message)s"
    setup_logging(level=logging.INFO, format_string=format_string)
    
    logger = logging.getLogger(LOGGER_NAME)
    handler = logger.handlers[0]
    assert handler.formatter._fmt == format_string


def test_setup_logging_custom_stream() -> None:
    """Test setting up logging with custom stream."""
    stream = StringIO()
    setup_logging(level=logging.INFO, stream=stream)
    
    logger = logging.getLogger(LOGGER_NAME)
    logger.info("Test message")
    
    stream.seek(0)
    output = stream.read()
    assert "Test message" in output


def test_setup_logging_removes_existing_handlers() -> None:
    """Test that setup_logging removes existing handlers."""
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(LOGGER_NAME)
    initial_handler_count = len(logger.handlers)
    
    setup_logging(level=logging.DEBUG)
    # Should have same number of handlers (removed old, added new)
    assert len(logger.handlers) == initial_handler_count


def test_logger_logs_messages() -> None:
    """Test that logger actually logs messages."""
    stream = StringIO()
    setup_logging(level=logging.INFO, stream=stream)
    
    logger = get_logger("test")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.debug("Debug message")  # Should not appear (level is INFO)
    
    stream.seek(0)
    output = stream.read()
    
    assert "Info message" in output
    assert "Warning message" in output
    assert "Error message" in output
    assert "Debug message" not in output  # Below INFO level


def test_logger_different_levels() -> None:
    """Test logger with different log levels."""
    stream = StringIO()
    
    # Test DEBUG level
    setup_logging(level=logging.DEBUG, stream=stream)
    logger = get_logger("test")
    logger.debug("Debug message")
    
    stream.seek(0)
    output = stream.read()
    assert "Debug message" in output
    
    # Test WARNING level
    stream = StringIO()
    setup_logging(level=logging.WARNING, stream=stream)
    logger = get_logger("test")
    logger.info("Info message")
    logger.warning("Warning message")
    
    stream.seek(0)
    output = stream.read()
    assert "Info message" not in output  # Below WARNING level
    assert "Warning message" in output


def test_logger_no_propagation() -> None:
    """Test that logger doesn't propagate to root logger."""
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(LOGGER_NAME)
    
    assert logger.propagate is False


def test_get_logger_after_setup() -> None:
    """Test getting logger after setup_logging."""
    from gaugid.logger import LOGGER_NAME
    setup_logging(level=logging.DEBUG)
    logger = get_logger("test_module")
    # Root gaugid logger has DEBUG; child loggers may inherit (level NOTSET)
    root_gaugid = logging.getLogger(LOGGER_NAME)
    assert root_gaugid.level == logging.DEBUG
    assert logger.name.startswith(LOGGER_NAME)
    assert len(root_gaugid.handlers) > 0


def test_setup_logging_multiple_times() -> None:
    """Test calling setup_logging multiple times."""
    setup_logging(level=logging.INFO)
    logger1 = logging.getLogger(LOGGER_NAME)
    
    setup_logging(level=logging.DEBUG)
    logger2 = logging.getLogger(LOGGER_NAME)
    
    # Should be the same logger instance
    assert logger1 is logger2
    # But level should be updated
    assert logger2.level == logging.DEBUG
