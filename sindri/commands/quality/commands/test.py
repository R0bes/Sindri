"""Test command."""

from pathlib import Path
from typing import Any, Dict

from sindri.commands.command import Command
from sindri.runner import AsyncExecutionEngine, CommandResult


class TestCommand(Command):
    """Run tests command."""

    def __init__(self):
        super().__init__(
            command_id="test",
            title="Test",
            description="Run tests",
        )

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """Execute test command with special handling for pytest exit codes."""
        from sindri.config import Command as ConfigCommand
        
        # Create a config command for pytest
        config_cmd = ConfigCommand(
            id=self.command_id,
            title=self.title,
            description=self.description,
            shell="python -m pytest",
        )
        
        # Run the command
        result = await engine.run_command(
            config_cmd,
            stream_callback=kwargs.get("stream_callback"),
        )
        
        # Pytest exit codes:
        # 0: All tests passed
        # 1-4: Tests failed or errors
        # 5: No tests collected (not an error)
        if result.exit_code == 5:
            # No tests found - treat as success with info message
            return CommandResult(
                command_id=self.command_id,
                exit_code=0,
                stdout=(
                    result.stdout
                    + "\n(No tests found - this is not an error)"
                ),
            )
        
        return result
