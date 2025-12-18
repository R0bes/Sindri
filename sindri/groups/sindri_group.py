"""Sindri command group - project setup and initialization."""

from __future__ import annotations

from sindri.core.group import CommandGroup


class SindriGroup(CommandGroup):
    """Sindri command group for project initialization."""

    def __init__(self) -> None:
        super().__init__(
            group_id="sindri",
            title="Sindri",
            description="Sindri project setup and initialization",
            order=0,
        )

    def get_commands(self):
        """Get all commands in this group.
        
        Currently empty - use 'sindri init' CLI command instead.
        """
        return []
