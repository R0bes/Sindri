"""Sindri command group - project setup and initialization."""

from __future__ import annotations

from sindri.core.command import ShellCommand
from sindri.core.group import CommandGroup


class SindriGroup(CommandGroup):
    """Sindri command group for project initialization and documentation."""

    def __init__(self) -> None:
        super().__init__(
            group_id="sindri",
            title="Sindri",
            description="Sindri project setup, initialization and documentation",
            order=0,
        )
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        """Create all Sindri commands."""
        return [
            ShellCommand(
                id="docs-setup",
                shell="pip install -e \".[docs]\"",
                title="Docs Setup",
                description="Install documentation dependencies (MkDocs)",
                group_id=self.id,
            ),
            ShellCommand(
                id="docs-preview",
                shell="mkdocs serve",
                title="Docs Preview",
                description="Start local MkDocs server for preview (http://127.0.0.1:8000)",
                group_id=self.id,
                watch=True,
            ),
            ShellCommand(
                id="docs-build",
                shell="mkdocs build",
                title="Docs Build",
                description="Build documentation site",
                group_id=self.id,
            ),
            ShellCommand(
                id="docs-build-strict",
                shell="mkdocs build --strict",
                title="Docs Build (Strict)",
                description="Build documentation site with strict mode (fails on warnings)",
                group_id=self.id,
            ),
            ShellCommand(
                id="docs-deploy",
                shell="mkdocs gh-deploy",
                title="Docs Deploy",
                description="Deploy documentation to GitHub Pages",
                group_id=self.id,
            ),
        ]

    def get_commands(self):
        """Get all commands in this group."""
        return self._commands
