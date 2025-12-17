"""Command execution result.

This module re-exports CommandResult from core for backward compatibility.
New code should import from sindri.core instead.
"""

from sindri.core.result import CommandResult

__all__ = ["CommandResult"]
