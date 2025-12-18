"""Central command registry with plugin support."""

from __future__ import annotations

import importlib.metadata
import logging
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from sindri.config.models import SindriConfig
    from sindri.core.command import Command
    from sindri.core.group import CommandGroup

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    Central registry for all commands.
    
    The registry provides:
    - Registration of individual commands and groups
    - Loading commands from TOML config
    - Plugin discovery via entry points
    - Command lookup by ID or alias
    - Namespace-based command resolution (e.g., "docker build" -> "docker-build")
    """

    # Entry point group for plugins
    PLUGIN_ENTRY_POINT = "sindri.groups"

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}
        self._groups: dict[str, CommandGroup] = {}
        self._aliases: dict[str, str] = {}  # alias -> primary_id
        self._namespace_map: dict[str, list[str]] = {}  # namespace -> [command_ids]

    @property
    def commands(self) -> dict[str, Command]:
        """Get all registered commands."""
        return self._commands.copy()

    @property
    def groups(self) -> dict[str, CommandGroup]:
        """Get all registered groups."""
        return self._groups.copy()

    def register(self, command: Command) -> None:
        """
        Register a single command.
        
        Args:
            command: Command to register
        """
        cmd_id = command.id
        
        if cmd_id in self._commands:
            logger.debug(f"Overwriting existing command: {cmd_id}")
        
        self._commands[cmd_id] = command
        
        # Update namespace map
        if "-" in cmd_id:
            namespace = cmd_id.split("-")[0]
            if namespace not in self._namespace_map:
                self._namespace_map[namespace] = []
            if cmd_id not in self._namespace_map[namespace]:
                self._namespace_map[namespace].append(cmd_id)
        
        # Register aliases if command has them
        if hasattr(command, "aliases"):
            for alias in command.aliases:
                self._aliases[alias] = cmd_id
        if hasattr(command, "_aliases"):
            for alias in command._aliases:
                self._aliases[alias] = cmd_id

    def register_alias(self, alias: str, command_id: str) -> None:
        """
        Register an alias for a command.
        
        Args:
            alias: Alias name
            command_id: Primary command ID
        """
        if command_id not in self._commands:
            raise ValueError(f"Cannot alias unknown command: {command_id}")
        self._aliases[alias] = command_id

    def register_group(self, group: CommandGroup) -> None:
        """
        Register a command group with all its commands.
        
        Args:
            group: CommandGroup to register
        """
        self._groups[group.id] = group
        
        for cmd in group.get_commands():
            # Set group_id on command if it has the attribute
            if hasattr(cmd, "group_id"):
                cmd.group_id = group.id
            elif hasattr(cmd, "_group_id"):
                cmd._group_id = group.id
            
            self.register(cmd)

    def load_from_config(self, config: SindriConfig) -> None:
        """
        Load commands from TOML config.
        
        Args:
            config: Parsed SindriConfig
        """
        from sindri.core.command import ShellCommand

        for config_cmd in config.commands:
            # Commands from config override built-in commands
            primary_id = config_cmd.primary_id
            # Remove existing command if it exists (config commands take precedence)
            if primary_id in self._commands:
                # Remove from commands dict
                del self._commands[primary_id]
                # Remove from aliases if it's an alias target
                aliases_to_remove = [alias for alias, target in self._aliases.items() if target == primary_id]
                for alias in aliases_to_remove:
                    del self._aliases[alias]
                # Remove from namespace map
                for namespace, cmd_ids in self._namespace_map.items():
                    if primary_id in cmd_ids:
                        cmd_ids.remove(primary_id)
            
            cmd = ShellCommand.from_config(config_cmd)
            self.register(cmd)

    def discover_plugins(self) -> list[str]:
        """
        Discover and load plugin command groups.
        
        Plugins are discovered via entry points in the 'sindri.groups' group.
        
        Returns:
            List of loaded plugin names
        """
        loaded = []
        
        try:
            entry_points = importlib.metadata.entry_points()
            
            # Handle both old and new entry_points API
            if hasattr(entry_points, "select"):
                # Python 3.10+
                plugin_eps = entry_points.select(group=self.PLUGIN_ENTRY_POINT)
            else:
                # Python 3.9
                plugin_eps = entry_points.get(self.PLUGIN_ENTRY_POINT, [])
            
            for ep in plugin_eps:
                try:
                    group_class = ep.load()
                    group_instance = group_class()
                    self.register_group(group_instance)
                    loaded.append(ep.name)
                    logger.info(f"Loaded plugin group: {ep.name}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin {ep.name}: {e}")
        
        except Exception as e:
            logger.warning(f"Plugin discovery failed: {e}")
        
        return loaded

    def discover_builtin_groups(self) -> list[str]:
        """
        Discover and load built-in command groups.
        
        Loads groups from sindri.groups module.
        
        Returns:
            List of loaded group IDs
        """
        loaded = []
        
        # Built-in groups: (group_id, new_module_path, class_name)
        builtin_groups = [
            ("sindri", "sindri.groups.sindri_group", "SindriGroup"),
            ("general", "sindri.groups.general", "GeneralGroup"),
            ("quality", "sindri.groups.quality", "QualityGroup"),
            ("application", "sindri.groups.application", "ApplicationGroup"),
            ("docker", "sindri.groups.docker", "DockerGroup"),
            ("compose", "sindri.groups.compose", "ComposeGroup"),
            ("git", "sindri.groups.git", "GitGroup"),
            ("version", "sindri.groups.version", "VersionGroup"),
            ("pypi", "sindri.groups.pypi", "PyPIGroup"),
        ]
        
        for group_id, module_path, class_name in builtin_groups:
            try:
                # Load from sindri.groups.*
                module = importlib.import_module(module_path)
                group_class = getattr(module, class_name)
                self.register_group(group_class())
                loaded.append(group_id)
                logger.debug(f"Loaded builtin group from {module_path}: {group_id}")
            except (ImportError, AttributeError) as e:
                logger.warning(f"Could not load builtin group {group_id} from {module_path}: {e}")
        
        return loaded

    def get(self, id_or_alias: str) -> Command | None:
        """
        Get command by ID or alias.
        
        Args:
            id_or_alias: Command ID or alias
            
        Returns:
            Command instance or None if not found
        """
        # Check aliases first
        if id_or_alias in self._aliases:
            id_or_alias = self._aliases[id_or_alias]
        
        return self._commands.get(id_or_alias)

    def resolve_parts(self, parts: list[str]) -> Command | None:
        """
        Resolve command from CLI parts.
        
        Handles various formats:
        - ["docker", "build"] -> "docker-build"
        - ["docker-build"] -> "docker-build"
        - ["d", "build"] -> "docker-build" (with alias support)
        - ["docker", "bp"] -> "docker-build_and_push" (action alias)
        - ["build"] -> "build" (direct lookup)
        
        Args:
            parts: List of command parts from CLI
            
        Returns:
            Command instance or None if not found
        """
        if not parts:
            return None
        
        # Namespace aliases
        namespace_aliases = {
            "d": "docker",
            "c": "compose",
            "g": "git",
            "v": "version",
            "q": "quality",
            "app": "application",
            "a": "application",
            "p": "pypi",
        }
        
        # Action aliases (short -> full)
        action_aliases = {
            "bp": "build_and_push",
        }
        
        # Expand first part if it's a namespace alias
        if parts[0] in namespace_aliases:
            parts = [namespace_aliases[parts[0]]] + parts[1:]
        
        # Expand action alias if present
        if len(parts) >= 2 and parts[1] in action_aliases:
            parts = [parts[0], action_aliases[parts[1]]] + parts[2:]
        
        # Try as full ID first (already hyphenated)
        if len(parts) == 1:
            if cmd := self.get(parts[0]):
                return cmd
        
        # Try joining with hyphen
        full_id = "-".join(parts)
        if cmd := self.get(full_id):
            return cmd
        
        # Try namespace lookup with space (for commands like "version show")
        if len(parts) >= 2:
            namespace, action = parts[0], parts[1]
            
            # Try with hyphen
            candidate = f"{namespace}-{action}"
            if cmd := self.get(candidate):
                return cmd
            
            # Try with space (for commands like "version show")
            candidate_space = f"{namespace} {action}"
            if cmd := self.get(candidate_space):
                return cmd
            
            # Try finding command by group (namespace) and action
            # (e.g., "quality test" -> find "test" in "quality" group)
            if namespace in self._groups:
                group_commands = self.get_by_group(namespace)
                for cmd in group_commands:
                    # Check if command ID matches action exactly
                    if cmd.id == action:
                        return cmd
                    # Check if action matches command ID without namespace prefix
                    if "-" in cmd.id:
                        cmd_action = cmd.id.split("-", 1)[1]
                        if cmd_action == action:
                            return cmd
                    if " " in cmd.id:
                        cmd_action = cmd.id.split(" ", 1)[1]
                        if cmd_action == action:
                            return cmd
        
        return None

    def get_by_group(self, group_id: str) -> list[Command]:
        """
        Get all commands in a group.
        
        Args:
            group_id: Group identifier
            
        Returns:
            List of commands in the group
        """
        if group_id not in self._groups:
            return []
        return self._groups[group_id].get_commands()

    def get_namespaces(self) -> list[str]:
        """Get all command namespaces."""
        return list(self._namespace_map.keys())

    def get_by_namespace(self, namespace: str) -> list[Command]:
        """
        Get all commands in a namespace.
        
        Args:
            namespace: Namespace (e.g., "docker", "git")
            
        Returns:
            List of commands in the namespace
        """
        cmd_ids = self._namespace_map.get(namespace, [])
        return [self._commands[cid] for cid in cmd_ids if cid in self._commands]

    def iter_commands(self) -> Iterator[Command]:
        """Iterate over all commands."""
        yield from self._commands.values()

    def iter_groups(self) -> Iterator[CommandGroup]:
        """Iterate over all groups."""
        yield from self._groups.values()

    def clear(self) -> None:
        """Clear all registered commands and groups."""
        self._commands.clear()
        self._groups.clear()
        self._aliases.clear()
        self._namespace_map.clear()

    def __len__(self) -> int:
        """Return number of registered commands."""
        return len(self._commands)

    def __contains__(self, command_id: str) -> bool:
        """Check if command is registered."""
        return command_id in self._commands or command_id in self._aliases


# Global registry instance
_global_registry: CommandRegistry | None = None


def get_registry() -> CommandRegistry:
    """Get the global command registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = CommandRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = None
