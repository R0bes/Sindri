"""Git command group - version control operations."""

from __future__ import annotations

from typing import Optional

from sindri.core.command import ShellCommand
from sindri.core.group import CommandGroup


class GitGroup(CommandGroup):
    """Git command group for version control operations."""

    def __init__(self, default_message: Optional[str] = None) -> None:
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
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        """Create all Git commands."""
        return [
            ShellCommand(
                id="git-status",
                shell="git status",
                title="Status",
                description="Show working tree status",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-add",
                shell="git add -A",
                title="Add All",
                description="Stage all changes",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-commit",
                shell=f"git add -A && git commit -m '{self.default_message}'",
                title="Commit",
                description="Stage and commit all changes",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-push",
                shell="git push",
                title="Push",
                description="Push commits to remote",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-pull",
                shell="git pull",
                title="Pull",
                description="Pull changes from remote",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-log",
                shell="git log --oneline -20",
                title="Log",
                description="Show recent commit history",
                group_id=self.id,
            ),
        ]

    def get_commands(self):
        """Get all commands in this group."""
        return self._commands
