"""Quality command group - linting, formatting, type checking."""

from sindri.core.command import ShellCommand
from sindri.core.group import CommandGroup


class QualityGroup(CommandGroup):
    """Code quality commands like linting, formatting, and type checking."""

    def __init__(self) -> None:
        super().__init__(
            group_id="quality",
            title="Quality",
            description="Code quality, linting, and formatting commands",
            order=2,
        )
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        return [
            ShellCommand(
                id="lint",
                shell="python -m ruff check .",
                title="Lint",
                description="Run ruff linter",
                group_id=self.id,
            ),
            ShellCommand(
                id="format",
                shell="python -m ruff format .",
                title="Format",
                description="Format code with ruff",
                group_id=self.id,
            ),
            ShellCommand(
                id="typecheck",
                shell="python -m mypy .",
                title="Type Check",
                description="Run mypy type checker",
                group_id=self.id,
            ),
            ShellCommand(
                id="test",
                shell="python -m pytest tests/",
                title="Test",
                description="Run pytest test suite",
                group_id=self.id,
            ),
            ShellCommand(
                id="test-cov",
                shell="python -m pytest --cov --cov-report=term --cov-report=html",
                title="Test with Coverage",
                description="Run tests with coverage report",
                group_id=self.id,
            ),
            ShellCommand(
                id="check",
                shell="python -m ruff check . && python -m ruff format --check . && python -m mypy .",
                title="Quality Check",
                description="Run all quality checks (lint, format check, typecheck)",
                group_id=self.id,
            ),
        ]

    def get_commands(self):
        return self._commands
