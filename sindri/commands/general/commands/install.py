"""Install command."""

from pathlib import Path

from sindri.commands.shell_command import ShellCommand
from sindri.utils.venv_helper import get_install_command


class InstallCommand(ShellCommand):
    """Install dependencies command."""
    def __init__(self):
        # Get intelligent default that uses .sindri/venv
        cwd = Path.cwd()
        shell = get_install_command(cwd)
        
        super().__init__(
            command_id="install",
            title="Install",
            description="Install dependencies",
            shell=shell,
        )

