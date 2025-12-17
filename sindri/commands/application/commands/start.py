"""Start command."""

from pathlib import Path

from sindri.commands.shell_command import ShellCommand
from sindri.utils.command_defaults import get_start_command


class StartCommand(ShellCommand):
    """Start application command."""

    def __init__(self):
        # Get intelligent default based on project
        cwd = Path.cwd()
        shell = get_start_command(cwd)
        
        super().__init__(
            command_id="start",
            title="Start",
            description="Start application",
            shell=shell,
        )

