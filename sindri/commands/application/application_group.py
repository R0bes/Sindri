"""Application command group."""

from sindri.commands.application.commands import (
    BuildCommand,
    ReCommand,
    RestartCommand,
    StartCommand,
    StopCommand,
)
from sindri.commands.command import Command
from sindri.commands.group import CommandGroup


class ApplicationGroup(CommandGroup):
    """Application command group."""

    def __init__(self):
        super().__init__(
            group_id="application",
            title="Application",
            description="Application lifecycle commands",
            order=2,
        )
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _initialize_commands(self) -> None:
        """Initialize commands for this group."""
        self._command_list = [
            RestartCommand(),
            ReCommand(),
            StartCommand(),
            StopCommand(),
            BuildCommand(),
        ]

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list

