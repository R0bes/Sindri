"""Build command."""

from pathlib import Path

from sindri.commands.shell_command import ShellCommand
from sindri.utils.command_defaults import get_build_command


class BuildCommand(ShellCommand):
    """Build application command."""

    def __init__(self):
        # Get intelligent default based on project
        cwd = Path.cwd()
        shell = get_build_command(cwd)
        
        super().__init__(
            command_id="build",
            title="Build",
            description="Build application",
            shell=shell,
        )

