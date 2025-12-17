"""Command execution result."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CommandResult:
    """Result of a command execution."""

    command_id: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.exit_code == 0

    def __repr__(self) -> str:
        status = "OK" if self.success else f"FAILED({self.exit_code})"
        return f"CommandResult({self.command_id}: {status}, {self.duration:.2f}s)"

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "command_id": self.command_id,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "duration": self.duration,
            "success": self.success,
            "metadata": self.metadata,
        }

    @classmethod
    def failure(
        cls,
        command_id: str,
        error: str,
        exit_code: int = 1,
    ) -> "CommandResult":
        """Create a failure result."""
        return cls(
            command_id=command_id,
            exit_code=exit_code,
            error=error,
        )

    @classmethod
    def dry_run(cls, command_id: str, shell: str) -> "CommandResult":
        """Create a dry-run result."""
        return cls(
            command_id=command_id,
            exit_code=0,
            stdout=f"[DRY RUN] Would execute: {shell}",
            metadata={"dry_run": True},
        )
