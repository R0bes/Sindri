"""Abstract base class for command implementations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from sindri.runner import AsyncExecutionEngine, CommandResult


class Command(ABC):
    """
    Abstract base class for command implementations.
    
    Commands are organized by groups and provide a structured way to implement
    custom command logic beyond simple shell execution.
    """
    
    def __init__(
        self,
        command_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize a command.
        
        Args:
            command_id: Unique identifier for the command
            title: Display title (defaults to command_id)
            description: Command description
        """
        self.command_id = command_id
        self.title = title or command_id
        self.description = description
    
    @abstractmethod
    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """
        Execute the command.
        
        Args:
            engine: Execution engine instance
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional command-specific arguments
            
        Returns:
            CommandResult with execution details
        """
        pass
    
    def validate(self, **kwargs: Any) -> Optional[str]:
        """
        Validate command parameters before execution.
        
        Args:
            **kwargs: Command parameters to validate
            
        Returns:
            Error message if validation fails, None otherwise
        """
        return None
    
    def get_dependencies(self) -> List[str]:
        """
        Get list of command IDs that this command depends on.
        
        Returns:
            List of command IDs
        """
        return []

