"""
Structured logging configuration.
"""

import sys
import logging
import structlog
from typing import Optional


def setup_logging(level: str = "INFO", json_output: bool = False):
    """
    Configure structured logging for the pipeline.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: Whether to output JSON format (for production)
    """
    
    # Map level string to logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_output:
        # JSON output for production/log aggregation
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Pretty console output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback
            )
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None):
    """Get a logger instance."""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()
