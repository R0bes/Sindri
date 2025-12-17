"""Setup command."""

from pathlib import Path

from sindri.commands.shell_command import ShellCommand
from sindri.utils.venv_helper import get_setup_command


class SetupCommand(ShellCommand):
    """Setup project command."""

    def __init__(self):
        # Get intelligent default that uses .sindri/venv
        cwd = Path.cwd()
        shell = get_setup_command(cwd)
        
        super().__init__(
            command_id="setup",
            title="Setup",
            description="Setup project",
            shell=shell,
        )

