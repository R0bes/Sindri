"""Structured logging setup for Sindri."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler

from sindri.utils.helper import get_project_name


def setup_logging(
    json_logs: bool = False,
    verbose: bool = False,
    project_path: Optional[Path] = None,
) -> structlog.BoundLogger:
    """
    Set up structured logging for Sindri.
    
    Args:
        json_logs: Whether to output JSON logs
        verbose: Whether to enable verbose logging
        project_path: Path to project for log file location
        
    Returns:
        Configured logger instance
    """
    log_level = "DEBUG" if verbose else "INFO"
    
    # Configure processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if json_logs:
        # JSON output
        processors.append(structlog.processors.JSONRenderer())
        RichHandler(
            console=Console(file=sys.stderr),
            show_path=False,
            rich_tracebacks=True,
        )
    else:
        # Human-readable output with colors
        processors.append(structlog.dev.ConsoleRenderer())
        RichHandler(
            console=Console(stderr=True),
            show_path=False,
            rich_tracebacks=True,
            markup=True,
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set up file logging if project path is provided
    logger = structlog.get_logger()
    
    if project_path:
        log_dir = _get_log_dir(project_path)
        log_file = _get_log_file(log_dir)
        
        # Add file handler
        _create_file_handler(log_file, json_logs)
        # Note: structlog doesn't directly support file handlers in the same way,
        # but we can add a processor to write to file
        logger = logger.bind(log_file=str(log_file))
    
    return logger


def _get_log_dir(project_path: Path) -> Path:
    """Get the log directory for a project."""
    project_name = get_project_name(project_path)
    log_base = Path.home() / ".sindri" / "logs" / project_name
    log_base.mkdir(parents=True, exist_ok=True)
    return log_base


def _get_log_file(log_dir: Path) -> Path:
    """Get the log file path with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"sindri_{timestamp}.log"


def _create_file_handler(log_file: Path, json_format: bool) -> None:
    """Create a file handler for logging."""
    # This is a placeholder - actual file logging would be handled
    # by adding a processor to structlog that writes to the file
    log_file.parent.mkdir(parents=True, exist_ok=True)
    # File will be written by log processors


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a logger instance.
    
    Args:
        name: Optional logger name
        
    Returns:
        Logger instance
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()

