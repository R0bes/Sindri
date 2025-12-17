"""Coverage command."""

from sindri.commands.shell_command import ShellCommand


class CovCommand(ShellCommand):
    """Run tests with code coverage."""

    def __init__(self):
        super().__init__(
            command_id="cov",
            shell="python -m pytest --cov=sindri --cov-report=term",
            title="Coverage",
            description="Run tests with code coverage",
        )

