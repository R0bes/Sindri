"""Abstract base class for command groups."""

from abc import ABC, abstractmethod
from typing import List, Optional

from sindri.commands.command import Command


class CommandGroup(ABC):
    """
    Abstract base class for command groups.
    
    Command groups organize commands by category and provide
    metadata about the group.
    """
    
    def __init__(
        self,
        group_id: str,
        title: str,
        description: Optional[str] = None,
        order: Optional[int] = None,
    ):
        """
        Initialize a command group.
        
        Args:
            group_id: Unique identifier for the group
            title: Display title
            description: Group description
            order: Sort order (lower first)
        """
        self.group_id = group_id
        self.title = title
        self.description = description
        self.order = order
        self._commands: List[Command] = []
    
    @abstractmethod
    def get_commands(self) -> List[Command]:
        """
        Get all commands in this group.

        Returns:
            List of Command instances
        """
    
    def add_command(self, command: Command) -> None:
        """Add a command to this group."""
        self._commands.append(command)
    
    def get_command(self, command_id: str) -> Optional[Command]:
        """Get a command by ID from this group."""
        for cmd in self.get_commands():
            if cmd.command_id == command_id:
                return cmd
        return None
    
    @property
    def commands(self) -> List[Command]:
        """Get all commands in this group."""
        return self.get_commands()
    
    def __repr__(self) -> str:
        cmd_count = len(self.get_commands())
        return (
            f"CommandGroup(id={self.group_id}, "
            f"title={self.title}, commands={cmd_count})"
        )

