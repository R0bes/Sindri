"""Application command group - run, start, stop."""

from sindri.core.command import ShellCommand
from sindri.core.group import CommandGroup


class ApplicationGroup(CommandGroup):
    """Application runtime commands."""

    def __init__(self) -> None:
        super().__init__(
            group_id="application",
            title="Application",
            description="Application run and management commands",
            order=3,
        )
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        return [
            ShellCommand(
                id="run",
                shell="python -m ${project_name}",
                title="Run",
                description="Run the application",
                group_id=self.id,
            ),
            ShellCommand(
                id="dev",
                shell="python -m ${project_name}",
                title="Dev",
                description="Run in development mode",
                group_id=self.id,
                env={"DEBUG": "1"},
            ),
        ]

    def get_commands(self):
        return self._commands
