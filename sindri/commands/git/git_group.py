"""Git command group."""

from typing import Optional

from sindri.commands.command import Command
from sindri.commands.group import CommandGroup
from sindri.commands.shell_command import ShellCommand


class GitGroup(CommandGroup):
    """
    Git command group with shared logic for Git operations.

    Provides common functionality for Git commands.
    """

    def __init__(self, default_message: Optional[str] = None):
        """
        Initialize Git command group.

        Args:
            default_message: Default commit message
        """
        super().__init__(
            group_id="git",
            title="Git",
            description="Git version control commands",
            order=5,
        )
        self.default_message = default_message or "Update"
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _get_commit_cmd(self, message: Optional[str] = None) -> str:
        """
        Build git commit command.

        Args:
            message: Commit message (defaults to group default)

        Returns:
            Full git commit command
        """
        msg = message or self.default_message
        return f"git add -A && git commit -m '{msg}'"

    def _initialize_commands(self) -> None:
        """Initialize Git commands."""
        self._command_list = [

            ShellCommand(
                command_id="git-commit",
                shell=self._get_commit_cmd(),
                title="Commit",
                description="Commit changes",
            ),

            ShellCommand(
                command_id="git-push",
                shell="git push",
                title="Push",
                description="Push changes to remote",
            ),
            
        ]

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list

