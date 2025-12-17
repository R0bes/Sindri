"""Shell command implementation."""

from pathlib import Path
from typing import Any, Dict, Optional

from sindri.commands.command import Command
from sindri.runner import AsyncExecutionEngine, CommandResult


class ShellCommand(Command):
    """
    Command implementation that executes a shell command.
    
    This is the default implementation for commands defined in the config file.
    """
    
    def __init__(
        self,
        command_id: str,
        shell: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
    ):
        """
        Initialize a shell command.

        Args:
            command_id: Unique identifier for the command
            shell: Shell command to execute (defaults to NotImplementedError)
            title: Display title (defaults to command_id)
            description: Command description
            cwd: Working directory (relative to config file)
            env: Environment variables
            timeout: Timeout in seconds
            retries: Number of retries on failure
        """
        super().__init__(command_id, title, description)
        if shell is None:
            shell = f"python -c \"raise NotImplementedError('{self.title} command not implemented')\""
        self.shell = shell
        self.cwd = cwd
        self.env = env or {}
        self.timeout = timeout
        self.retries = retries
    
    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """
        Execute the shell command.
        
        Args:
            engine: Execution engine instance
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional arguments (ignored for shell commands)
            
        Returns:
            CommandResult with execution details
        """
        # Merge environment variables
        merged_envs = {**env, **self.env}
        
        # Resolve working directory
        resolved_cwd = cwd
        if self.cwd:
            resolved_cwd = (cwd / self.cwd).resolve()
            if not resolved_cwd.exists():
                return CommandResult(
                    self.command_id,
                    1,
                    error=f"Working directory does not exist: {resolved_cwd}",
                )
        
        # Create a temporary Command model for the engine
        from sindri.config import Command as ConfigCommand
        
        # Expand templates
        shell_cmd = engine._expand_templates(self.shell)
        
        # Create config command model
        config_cmd = ConfigCommand(
            id=self.command_id,
            title=self.title,
            description=self.description,
            shell=shell_cmd,
            cwd=self.cwd,
            env=merged_envs,
            timeout=self.timeout,
            retries=self.retries,
        )
        
        # Use engine's run_command method
        return await engine.run_command(
            config_cmd,
            stream_callback=kwargs.get("stream_callback"),
        )

