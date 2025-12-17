"""Sindri command group for project setup and initialization."""

from sindri.commands.command import Command
from sindri.commands.group import CommandGroup


class SindriGroup(CommandGroup):
    """Sindri command group for project initialization and setup."""

    def __init__(self):
        super().__init__(
            group_id="sindri",
            title="Sindri",
            description="Sindri project setup and initialization",
            order=0,  # First group
        )
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _initialize_commands(self) -> None:
        """Initialize Sindri commands."""
        # No commands in sindri group anymore (use 'sindri init' instead)
        self._command_list = []

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list

