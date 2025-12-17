"""Validate command."""

from pathlib import Path

from sindri.commands.shell_command import ShellCommand
from sindri.utils.command_defaults import get_validate_command


class ValidateCommand(ShellCommand):
    """Validate project command."""

    def __init__(self):
        # Get intelligent default based on project
        cwd = Path.cwd()
        shell = get_validate_command(cwd)
        
        super().__init__(
            command_id="validate",
            title="Validate",
            description="Validate project",
            shell=shell,
        )

