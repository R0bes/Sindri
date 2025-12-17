"""Version command."""

from pathlib import Path
from typing import Any, Dict

from sindri.commands.command import Command
from sindri.runner import AsyncExecutionEngine, CommandResult
from sindri.utils.helper import (
    get_project_name_from_pyproject,
    get_project_version_from_pyproject,
)


class VersionCommand(Command):
    """Show version information command."""

    def __init__(self):
        super().__init__(
            command_id="version",
            title="Version",
            description="Show version information",
        )

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """
        Execute version command.

        Args:
            engine: Execution engine instance
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional arguments

        Returns:
            CommandResult with version information
        """
        # Get project name and version from pyproject.toml
        project_name = get_project_name_from_pyproject(cwd)
        version = get_project_version_from_pyproject(cwd)

        if project_name and version:
            output = f"{project_name} {version}"
        elif version:
            output = version
        else:
            output = "Version information not available"

        return CommandResult(
            self.command_id,
            0,
            stdout=output,
        )

