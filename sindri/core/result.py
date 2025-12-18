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
        status = "SUCCESS" if self.success else f"FAILED({self.exit_code})"
        return f"CommandResult({self.command_id}: {status}, {self.duration:.2f}s)"
    
    def __bool__(self) -> bool:
        """Boolean conversion: True if successful, False otherwise."""
        return self.success
    
    @property
    def output(self) -> str:
        """Get combined stdout and stderr output."""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(parts)
    
    def raise_on_error(self, message_prefix: Optional[str] = None) -> None:
        """
        Raise RuntimeError if command failed.
        
        Args:
            message_prefix: Optional prefix for error message
            
        Raises:
            RuntimeError: If command failed
        """
        if self.success:
            return
        
        if self.error:
            msg = self.error
        elif self.stderr:
            msg = self.stderr
        else:
            msg = f"Command failed with exit code {self.exit_code}"
        
        if message_prefix:
            msg = f"{message_prefix}: {msg}"
        
        raise RuntimeError(msg)

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
