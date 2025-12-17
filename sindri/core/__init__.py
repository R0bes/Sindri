"""Core module for Sindri - foundational types and utilities."""

from sindri.core.result import CommandResult
from sindri.core.context import ExecutionContext
from sindri.core.templates import TemplateEngine, get_template_engine
from sindri.core.command import Command, ShellCommand, CustomCommand, is_shell_command
from sindri.core.group import CommandGroup
from sindri.core.registry import CommandRegistry, get_registry, reset_registry
from sindri.core.shell_runner import run_shell_command, run_shell_commands_parallel

__all__ = [
    # Result
    "CommandResult",
    # Context
    "ExecutionContext",
    # Templates
    "TemplateEngine",
    "get_template_engine",
    # Commands
    "Command",
    "ShellCommand",
    "CustomCommand",
    "is_shell_command",
    # Groups
    "CommandGroup",
    # Registry
    "CommandRegistry",
    "get_registry",
    "reset_registry",
    # Shell execution
    "run_shell_command",
    "run_shell_commands_parallel",
]
