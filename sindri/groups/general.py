"""General command group - setup, install, etc."""

from sindri.core.command import ShellCommand
from sindri.core.group import CommandGroup


class GeneralGroup(CommandGroup):
    """General project commands like setup and install."""

    def __init__(self) -> None:
        super().__init__(
            group_id="general",
            title="General",
            description="General project setup and installation commands",
            order=1,
        )
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        return [
            ShellCommand(
                id="setup",
                shell="pip install -e '.[dev]' --break-system-packages",
                title="Setup",
                description="Install project in development mode with dev dependencies",
                group_id=self.id,
            ),
            ShellCommand(
                id="install",
                shell="pip install -e . --break-system-packages",
                title="Install",
                description="Install project in development mode",
                group_id=self.id,
            ),
        ]

    def get_commands(self):
        return self._commands
