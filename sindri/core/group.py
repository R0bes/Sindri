"""Command group base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sindri.core.command import Command


class CommandGroup(ABC):
    """
    Base class for command groups.
    
    Command groups organize related commands together and provide
    metadata about the group.
    """

    def __init__(
        self,
        group_id: str,
        title: str,
        description: str | None = None,
        order: int | None = None,
    ) -> None:
        """
        Initialize a command group.
        
        Args:
            group_id: Unique identifier for the group
            title: Display title
            description: Group description
            order: Sort order (lower first)
        """
        self._id = group_id
        self._title = title
        self._description = description
        self._order = order

    @property
    def id(self) -> str:
        """Get group identifier."""
        return self._id

    @property
    def title(self) -> str:
        """Get group title."""
        return self._title

    @property
    def description(self) -> str | None:
        """Get group description."""
        return self._description

    @property
    def order(self) -> int | None:
        """Get sort order."""
        return self._order

    @abstractmethod
    def get_commands(self) -> list[Command]:
        """
        Get all commands in this group.
        
        Returns:
            List of Command instances
        """
        ...

    def get_command(self, command_id: str) -> Command | None:
        """
        Get a command by ID from this group.
        
        Args:
            command_id: Command identifier
            
        Returns:
            Command instance or None if not found
        """
        for cmd in self.get_commands():
            if cmd.id == command_id:
                return cmd
        return None

    def __repr__(self) -> str:
        cmd_count = len(self.get_commands())
        return f"CommandGroup(id={self._id}, title={self._title}, commands={cmd_count})"
