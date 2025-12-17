"""Version command group."""

from sindri.commands.command import Command
from sindri.commands.group import CommandGroup
from sindri.commands.version.commands import (
    VersionBumpCommand,
    VersionShowCommand,
    VersionTagCommand,
)


class VersionGroup(CommandGroup):
    """Version command group."""

    def __init__(self):
        super().__init__(
            group_id="version",
            title="Version",
            description="Version management commands",
            order=2,
        )
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _initialize_commands(self) -> None:
        """Initialize version commands."""
        self._command_list = [
            VersionShowCommand(),
            VersionBumpCommand(),
            VersionTagCommand(),
        ]

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list

