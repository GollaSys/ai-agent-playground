"""Logging configuration for the simulator."""

import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logging(
    name: Optional[str] = None,
    level: str = "INFO",
    log_format: str = "detailed",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> logger:
    """Set up logging configuration for the simulator.
    
    Args:
        name: Logger name (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format style ("simple", "detailed", "json")
        log_file: Path to log file (optional)
        enable_console: Whether to log to console
    
    Returns:
        Configured logger instance
    """
    # Remove default handler
    logger.remove()
    
    # Define formats
    formats = {
        "simple": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        "detailed": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        "json": "{\"time\": \"{time:YYYY-MM-DD HH:mm:ss.SSS}\", \"level\": \"{level}\", \"module\": \"{name}\", \"function\": \"{function}\", \"line\": {line}, \"message\": \"{message}\"}"
    }
    
    format_str = formats.get(log_format, formats["detailed"])
    
    # Add console handler if enabled
    if enable_console:
        logger.add(
            sys.stderr,
            format=format_str,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=format_str,
            level=level,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    # Set up automatic log file if environment variable is set
    if "SIMULATOR_LOG_FILE" in os.environ:
        auto_log_file = os.environ["SIMULATOR_LOG_FILE"]
        logger.add(
            auto_log_file,
            format=format_str,
            level=level,
            rotation="10 MB",
            retention="1 week",
            compression="zip"
        )
    
    # Add performance logging for debug level
    if level == "DEBUG":
        import time
        import functools
        
        def log_performance(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                logger.debug(f"{func.__name__} took {end_time - start_time:.4f} seconds")
                return result
            return wrapper
        
        # Store the decorator for later use
        logger.performance = log_performance
    
    if name:
        return logger.bind(name=name)
    
    return logger


def configure_from_env() -> logger:
    """Configure logging from environment variables."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "detailed").lower()
    log_file = os.getenv("LOG_FILE")
    enable_console = os.getenv("LOG_CONSOLE", "true").lower() == "true"
    
    return setup_logging(
        level=level,
        log_format=log_format,
        log_file=log_file,
        enable_console=enable_console
    )


# Create a default logger instance
default_logger = configure_from_env()