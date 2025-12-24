"""Logging configuration with daily rotation based on KST (Korea Standard Time)"""
import logging
import os
from datetime import datetime, timezone, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))

# Log directory
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


class KSTTimedRotatingFileHandler(TimedRotatingFileHandler):
    """TimedRotatingFileHandler that rotates at midnight KST."""

    def computeRollover(self, currentTime):
        """Compute rollover time based on KST midnight."""
        # Get current time in KST
        now_kst = datetime.fromtimestamp(currentTime, tz=KST)

        # Calculate next midnight in KST
        next_midnight_kst = now_kst.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        # Convert back to timestamp
        return int(next_midnight_kst.timestamp())


def setup_logging(name: str = "backend") -> logging.Logger:
    """
    Set up logging with both console and file handlers.

    Args:
        name: Logger name (used for log file naming)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Log format
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with daily rotation at KST midnight
    log_file = LOG_DIR / f"{name}.log"
    file_handler = KSTTimedRotatingFileHandler(
        filename=str(log_file),
        when='midnight',
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"  # Log file suffix format
    logger.addHandler(file_handler)

    return logger


# Default logger
logger = setup_logging("backend")
