"""Restart alias command."""

from pathlib import Path

from sindri.commands.shell_command import ShellCommand
from sindri.utils.command_defaults import get_restart_command, get_start_command, get_stop_command


class ReCommand(ShellCommand):
    """Restart application command (alias)."""

    def __init__(self):
        # Get intelligent default based on project
        cwd = Path.cwd()
        start_cmd = get_start_command(cwd)
        stop_cmd = get_stop_command(cwd, start_cmd)
        shell = get_restart_command(cwd, start_cmd, stop_cmd)
        
        super().__init__(
            command_id="re",
            title="Rebuild+Restart",
            description="Restart application (alias)",
            shell=shell,
        )

