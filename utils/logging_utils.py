"""
Logging utilities for ClassCast project.
Provides consistent logging across all modules.
"""
import logging
import sys
from pathlib import Path

import config


def setup_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger instance.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    # Set level based on config
    level = logging.DEBUG if config.DEBUG_LOGGING else logging.INFO
    logger.setLevel(level)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def log_step(logger: logging.Logger, step_name: str):
    """Log a major pipeline step."""
    logger.info("=" * 60)
    logger.info(f"STEP: {step_name}")
    logger.info("=" * 60)
