"""Registry for implemented commands from Python classes."""

from typing import TYPE_CHECKING, Dict, Optional

from sindri.config.models import Command as ConfigCommand

if TYPE_CHECKING:
    from sindri.commands.command import Command
    from sindri.config.models import SindriConfig


def get_implemented_commands(
    group_ids: Optional[list[str]] = None,
) -> Dict[str, "Command"]:  # noqa: F821
    """
    Get implemented commands from Python classes.
    
    Only loads commands from specified groups if group_ids is provided.
    This is faster when only certain groups are needed.

    Args:
        group_ids: Optional list of group IDs to load. If None, loads all groups.

    Returns:
        Dictionary mapping command_id -> Command instance
    """
    # Import here to avoid circular imports
    from sindri.commands import (
        ApplicationGroup,
        ComposeGroup,
        DockerGroup,
        GeneralGroup,
        GitGroup,
        PyPIGroup,
        QualityGroup,
        SindriGroup,
        VersionGroup,
    )
    from sindri.commands.command import Command

    commands: Dict[str, Command] = {}

    # Map group IDs to group classes
    group_classes = {
        "sindri": SindriGroup,
        "general": GeneralGroup,
        "quality": QualityGroup,
        "application": ApplicationGroup,
        "docker": DockerGroup,
        "compose": ComposeGroup,
        "git": GitGroup,
        "version": VersionGroup,
        "pypi": PyPIGroup,
    }

    # Core groups (always available)
    core_group_ids = ["sindri", "general", "quality", "application"]
    
    # Optional groups (may not be available if extras not installed)
    optional_group_ids = ["docker", "compose", "git", "version", "pypi"]
    
    # Load commands from specified groups only
    if group_ids:
        groups_to_load = []
        for gid in group_ids:
            if gid in group_classes:
                try:
                    groups_to_load.append(group_classes[gid]())
                except (ImportError, AttributeError, TypeError) as e:
                    # Optional group not available (graceful degradation)
                    pass
    else:
        # Load all groups if no filter specified
        groups_to_load = []
        
        # Always load core groups
        for gid in core_group_ids:
            if gid in group_classes:
                try:
                    groups_to_load.append(group_classes[gid]())
                except (ImportError, AttributeError, TypeError):
                    pass
        
        # Try to load optional groups (graceful degradation)
        for gid in optional_group_ids:
            if gid in group_classes:
                try:
                    groups_to_load.append(group_classes[gid]())
                except (ImportError, AttributeError, TypeError):
                    # Optional group not available
                    pass

    for group in groups_to_load:
        for cmd in group.get_commands():
            # Use command_id as key (primary ID from Command class)
            primary_id = str(cmd.command_id)
            if primary_id not in commands:
                commands[primary_id] = cmd

            # Also register all aliases if the command has them
            # Note: Command classes use command_id, not id
            # We need to check if there are multiple IDs defined

    return commands


def is_custom_command(impl_command: "Command") -> bool:  # noqa: F821
    """
    Check if a command is a custom command (not a ShellCommand).
    
    Args:
        impl_command: Implemented Command instance
        
    Returns:
        True if the command is a custom command (needs direct execution)
    """
    from sindri.commands.shell_command import ShellCommand
    return not isinstance(impl_command, ShellCommand)


def convert_to_config_command(
    impl_command: "Command",  # noqa: F821
    config: Optional["SindriConfig"] = None,  # noqa: F821
) -> ConfigCommand:
    """
    Convert an implemented Command to a ConfigCommand.

    Args:
        impl_command: Implemented Command instance
        config: Optional SindriConfig for context (unused for now)

    Returns:
        ConfigCommand instance
    """
    _ = config  # Unused for now, but may be needed in future
    # Get shell command if it's a ShellCommand
    shell = ""
    if hasattr(impl_command, "shell"):
        shell = impl_command.shell
    else:
        # Default NotImplementedError
        shell = (
            f"python -c \"raise NotImplementedError('{impl_command.title} "
            "command not implemented')\""
        )

    # Use command_id as the ID (it's a string in Command classes)
    command_id = impl_command.command_id

    return ConfigCommand(
        id=command_id,
        title=impl_command.title,
        description=impl_command.description,
        shell=shell,
        cwd=getattr(impl_command, "cwd", None),
        env=getattr(impl_command, "env", None),
        timeout=getattr(impl_command, "timeout", None),
        retries=getattr(impl_command, "retries", None),
    )

