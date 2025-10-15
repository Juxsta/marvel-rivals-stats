"""Logging configuration utilities.

This module provides standardized logging setup across all modules,
with consistent formatting and both file and console output.
"""

import logging
from pathlib import Path


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Set up a logger with standardized configuration.

    Creates a logger with both file and console handlers, using a consistent
    format across the application. Logs are written to logs/app.log and also
    output to stdout.

    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Defaults to INFO.

    Returns:
        Configured logger instance

    Example:
        >>> from src.utils.logging_config import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing started")
    """
    # Create logger
    logger = logging.getLogger(name)

    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Define log format
    log_format = "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # File handler - writes to logs/app.log
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler - writes to stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.debug(f"Logger '{name}' configured with level {level}")

    return logger
