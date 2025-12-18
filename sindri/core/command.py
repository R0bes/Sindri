"""
Unified Command Protocol and implementations.

This module defines the core Command protocol that all commands must implement,
whether they come from TOML config, Python code, or plugins.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sindri.core.context import ExecutionContext
    from sindri.core.result import CommandResult


@runtime_checkable
class Command(Protocol):
    """
    Unified Command Protocol.
    
    All commands (shell-based, custom, plugin) implement this protocol.
    Using Protocol instead of ABC allows for more flexibility - any class
    with matching attributes/methods satisfies the protocol.
    
    Attributes:
        id: Unique command identifier (e.g., 'docker-build')
        title: Human-readable title
        description: Optional description
        group_id: Optional group membership
    """

    @property
    def id(self) -> str:
        """Unique command identifier."""
        ...

    @property
    def title(self) -> str:
        """Human-readable title."""
        ...

    @property
    def description(self) -> str | None:
        """Optional description."""
        ...

    @property
    def group_id(self) -> str | None:
        """Optional group membership."""
        ...

    def get_shell(self, ctx: ExecutionContext) -> str | None:
        """
        Return shell command string.
        
        Returns None if command requires custom execution logic.
        Template variables should NOT be expanded here - the executor handles that.
        
        Args:
            ctx: Execution context
            
        Returns:
            Shell command string or None for custom commands
        """
        ...

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """
        Execute the command.
        
        Default implementations should run get_shell() via the execution engine.
        Override for custom execution logic.
        
        Args:
            ctx: Execution context with all runtime parameters
            
        Returns:
            CommandResult with execution details
        """
        ...

    def validate(self, ctx: ExecutionContext) -> str | None:
        """
        Validate command can run in given context.
        
        Args:
            ctx: Execution context
            
        Returns:
            Error message if invalid, None if valid
        """
        ...


@dataclass
class ShellCommand:
    """
    Default implementation for shell-based commands.
    
    This is the standard implementation for commands defined in TOML config
    or simple shell commands defined in Python.
    """

    id: str
    shell: str
    title: str | None = None
    description: str | None = None
    group_id: str | None = None
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    env_profile: str | None = None
    timeout: int | None = None
    retries: int | None = None
    tags: list[str] = field(default_factory=list)
    watch: bool = False
    
    # Support for multiple IDs (aliases)
    _aliases: list[str] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Set title to id if not provided."""
        if self.title is None:
            self.title = self.id

    @property
    def aliases(self) -> list[str]:
        """Get command aliases."""
        return self._aliases

    @aliases.setter
    def aliases(self, value: list[str]) -> None:
        """Set command aliases."""
        self._aliases = value

    @property
    def all_ids(self) -> list[str]:
        """Get all command IDs including aliases."""
        return [self.id] + self._aliases

    def get_shell(self, ctx: ExecutionContext) -> str:
        """Return shell command string."""
        return self.shell

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """
        Execute the shell command.
        
        Uses the execution engine from the context.
        """
        import structlog
        from sindri.core.result import CommandResult
        
        logger = structlog.get_logger(__name__)
        
        logger.debug("Executing ShellCommand", command_id=self.id, ctx_cwd=str(ctx.cwd))
        
        # Get shell command (not expanded yet)
        shell = self.get_shell(ctx)
        logger.debug("Got shell command", command_id=self.id, shell=shell)
        
        # Expand templates
        expanded_shell = ctx.expand_templates(shell)
        logger.debug("Expanded shell command", command_id=self.id, expanded_shell=expanded_shell)
        
        # Resolve working directory
        cwd = ctx.cwd
        if self.cwd:
            cwd = ctx.resolve_path(self.cwd)
            if not cwd.exists():
                logger.warning("Working directory does not exist", command_id=self.id, cwd=str(cwd))
                return CommandResult.failure(
                    self.id,
                    f"Working directory does not exist: {cwd}",
                )
        
        logger.debug("Resolved working directory", command_id=self.id, cwd=str(cwd), cwd_exists=cwd.exists())
        
        # Merge environment variables
        env = ctx.get_env(self.env_profile)
        env.update(self.env)
        logger.debug("Merged environment", command_id=self.id, env_keys=len(env), has_virtual_env="VIRTUAL_ENV" in env)
        
        # Check for dry run
        if ctx.dry_run:
            logger.debug("Dry run mode", command_id=self.id)
            return CommandResult.dry_run(self.id, expanded_shell)
        
        # Execute via shell runner
        from sindri.core.shell_runner import run_shell_command
        
        logger.debug("Calling run_shell_command", command_id=self.id, cwd=str(cwd))
        result = await run_shell_command(
            command_id=self.id,
            shell=expanded_shell,
            cwd=cwd,
            env=env,
            timeout=self.timeout or ctx.timeout,
            stream_callback=ctx.stream_callback,
        )
        logger.debug("Command execution completed", command_id=self.id, exit_code=result.exit_code, success=result.success)
        return result

    def validate(self, ctx: ExecutionContext) -> str | None:
        """Validate command can run."""
        if self.cwd:
            cwd = ctx.resolve_path(self.cwd)
            if not cwd.exists():
                return f"Working directory does not exist: {cwd}"
        return None

    @classmethod
    def from_config(cls, config_cmd: Any) -> ShellCommand:
        """
        Create ShellCommand from config Command model.
        
        Args:
            config_cmd: Command from sindri.config.models
            
        Returns:
            ShellCommand instance
        """
        # Handle id being string or list
        if isinstance(config_cmd.id, list):
            primary_id = config_cmd.id[0]
            aliases = config_cmd.id[1:] if len(config_cmd.id) > 1 else []
        else:
            primary_id = config_cmd.id
            aliases = []
        
        # Add explicit aliases
        if config_cmd.aliases:
            aliases.extend(config_cmd.aliases)

        cmd = cls(
            id=primary_id,
            shell=config_cmd.shell,
            title=config_cmd.title,
            description=config_cmd.description,
            cwd=config_cmd.cwd,
            env=dict(config_cmd.env) if config_cmd.env else {},
            env_profile=config_cmd.env_profile,
            timeout=config_cmd.timeout,
            retries=config_cmd.retries,
            tags=list(config_cmd.tags) if config_cmd.tags else [],
            watch=config_cmd.watch or False,
        )
        cmd._aliases = aliases
        return cmd


class CustomCommand:
    """
    Base class for commands with custom execution logic.
    
    Extend this class when you need to implement commands that
    cannot be expressed as simple shell commands.
    """

    def __init__(
        self,
        command_id: str,
        title: str | None = None,
        description: str | None = None,
        group_id: str | None = None,
    ) -> None:
        self._id = command_id
        self._title = title or command_id
        self._description = description
        self._group_id = group_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def group_id(self) -> str | None:
        return self._group_id

    @group_id.setter
    def group_id(self, value: str | None) -> None:
        self._group_id = value

    def get_shell(self, ctx: ExecutionContext) -> str | None:
        """Custom commands return None - they have custom execute logic."""
        return None

    @abstractmethod
    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """
        Execute the custom command.
        
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def validate(self, ctx: ExecutionContext) -> str | None:
        """Validate command can run. Override in subclasses if needed."""
        return None


def is_shell_command(cmd: Command) -> bool:
    """Check if a command is a simple shell command."""
    # Try to get shell - if it returns a string, it's a shell command
    # This avoids needing to check isinstance
    try:
        from sindri.core.context import ExecutionContext
        # Create minimal context for checking
        dummy_ctx = ExecutionContext(cwd=Path("."))
        shell = cmd.get_shell(dummy_ctx)
        return shell is not None
    except Exception:
        return False


from pathlib import Path
