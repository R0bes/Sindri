"""Async execution engine for Sindri commands.

This module provides the execution engine and result types.
CommandResult is now defined in sindri.core.result and re-exported here
for backward compatibility.
"""

from sindri.core.result import CommandResult
from sindri.runner.engine import AsyncExecutionEngine

__all__ = ["CommandResult", "AsyncExecutionEngine"]
