"""Version tag command."""

from pathlib import Path
from typing import Any, Dict

from sindri.commands.command import Command
from sindri.runner import AsyncExecutionEngine, CommandResult
from sindri.utils.helper import get_project_version_from_pyproject


class VersionTagCommand(Command):
    """Create version tag command."""

    def __init__(self):
        super().__init__(
            command_id="version tag",
            title="Tag",
            description="Create git tag for current version",
        )

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """
        Execute version tag command.

        Args:
            engine: Execution engine instance
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional arguments

        Returns:
            CommandResult with tag information
        """
        # Get current version
        version = get_project_version_from_pyproject(cwd)
        if not version:
            return CommandResult(
                self.command_id,
                1,
                error="Could not determine current version from pyproject.toml",
            )

        # Create git tag
        from sindri.config import Command as ConfigCommand

        tag_name = f"v{version}"
        tag_cmd = ConfigCommand(
            id=f"{self.command_id}-create",
            shell=f'git tag -a "{tag_name}" -m "Version {version}"',
        )

        stream_callback = kwargs.get("stream_callback")
        result = await engine.run_command(tag_cmd, stream_callback)

        if result.success:
            return CommandResult(
                self.command_id,
                0,
                stdout=f"Created tag: {tag_name}",
            )
        else:
            return CommandResult(
                self.command_id,
                result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                error=result.error or "Failed to create git tag",
            )

