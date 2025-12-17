"""Quality command group."""

from sindri.commands.command import Command
from sindri.commands.group import CommandGroup
from sindri.commands.quality.commands import (
    CovCommand,
    LintCommand,
    TestCommand,
    ValidateCommand,
)


class QualityGroup(CommandGroup):
    """Quality command group."""

    def __init__(self):
        super().__init__(
            group_id="quality",
            title="Quality",
            description="Code quality commands (test, lint, validate)",
            order=2,
        )
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _initialize_commands(self) -> None:
        """Initialize commands for this group."""
        self._command_list = [
            TestCommand(),
            CovCommand(),
            LintCommand(),
            ValidateCommand(),
        ]

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list

