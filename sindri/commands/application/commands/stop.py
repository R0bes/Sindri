"""Stop command."""

from pathlib import Path

from sindri.commands.shell_command import ShellCommand
from sindri.utils.command_defaults import get_start_command, get_stop_command


class StopCommand(ShellCommand):
    """Stop application command."""

    def __init__(self):
        # Get intelligent default based on project
        cwd = Path.cwd()
        start_cmd = get_start_command(cwd)
        shell = get_stop_command(cwd, start_cmd)
        
        super().__init__(
            command_id="stop",
            title="Stop",
            description="Stop application",
            shell=shell,
        )

