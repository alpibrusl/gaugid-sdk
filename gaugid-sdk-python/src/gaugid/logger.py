"""
Logging configuration for Gaugid SDK.

This module provides a centralized logger for the Gaugid SDK with proper
configuration and formatting.
"""

import logging
import sys
from typing import Optional

# Logger name for the SDK
LOGGER_NAME = "gaugid"

# Default log level
DEFAULT_LOG_LEVEL = logging.WARNING


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the Gaugid SDK.
    
    Args:
        name: Optional logger name (defaults to 'gaugid')
        
    Returns:
        Configured logger instance
    """
    logger_name = f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME
    return logging.getLogger(logger_name)


def setup_logging(
    level: int = DEFAULT_LOG_LEVEL,
    format_string: Optional[str] = None,
    stream: Optional[object] = None,
) -> None:
    """
    Set up logging configuration for the Gaugid SDK.
    
    Args:
        level: Log level (defaults to WARNING)
        format_string: Custom format string for log messages
        stream: Output stream (defaults to stderr)
        
    Example:
        ```python
        from gaugid.logger import setup_logging
        import logging
        
        # Enable debug logging
        setup_logging(level=logging.DEBUG)
        ```
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if stream is None:
        stream = sys.stderr
    
    # Configure root logger for gaugid
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False


# Initialize logger on module import
_logger = get_logger()
