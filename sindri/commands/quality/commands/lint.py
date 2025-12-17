"""Lint command."""

from pathlib import Path

from sindri.commands.shell_command import ShellCommand
from sindri.utils.command_defaults import get_lint_command


class LintCommand(ShellCommand):
    """Run linter command."""

    def __init__(self):
        # Get intelligent default based on project
        cwd = Path.cwd()
        shell = get_lint_command(cwd)
        
        super().__init__(
            command_id="lint",
            title="Lint",
            description="Run linter",
            shell=shell,
        )

