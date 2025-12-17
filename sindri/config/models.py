"""Pydantic models for Sindri configuration."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, PrivateAttr, field_validator, model_validator


class CommandDependency(BaseModel):
    """Dependency configuration for a command."""

    before: Optional[List[str]] = Field(
        default=None, description="Commands to run before this command"
    )
    after: Optional[List[str]] = Field(
        default=None, description="Commands to run after this command"
    )


class Command(BaseModel):
    """A command definition."""

    id: str | List[str] = Field(
        description="Unique identifier(s) for the command. Can be a string or list of strings (first is primary ID)"
    )
    title: Optional[str] = Field(
        default=None, description="Display title (defaults to first id)"
    )
    description: Optional[str] = Field(default=None, description="Command description")
    shell: str = Field(description="Shell command to execute")
    cwd: Optional[str] = Field(
        default=None, description="Working directory (relative to config file)"
    )
    env: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables (command-specific)"
    )
    env_profile: Optional[str] = Field(
        default=None,
        description="Environment profile (dev, test, prod) - uses project env vars",
    )
    tags: Optional[List[str]] = Field(default=None, description="Tags for filtering")
    aliases: Optional[List[str]] = Field(
        default=None, description="Alternative command IDs (aliases)"
    )
    dependencies: Optional[CommandDependency] = Field(
        default=None, description="Command dependencies"
    )
    watch: Optional[bool] = Field(
        default=False, description="Whether this is a watch/tail command"
    )
    timeout: Optional[int] = Field(default=None, description="Timeout in seconds")
    retries: Optional[int] = Field(
        default=None, description="Number of retries on failure"
    )

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, v: Any) -> str | List[str]:
        """Normalize id to string or list of strings."""
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return [str(item) for item in v]
        return str(v)

    @model_validator(mode="after")
    def set_title_default(self) -> "Command":
        """Set title to first id if not provided."""
        if self.title is None:
            if isinstance(self.id, list):
                self.title = self.id[0] if self.id else ""
            else:
                self.title = self.id
        return self

    @property
    def primary_id(self) -> str:
        """Get the primary command ID (first in list or the id itself)."""
        if isinstance(self.id, list):
            return self.id[0] if self.id else ""
        return self.id

    @property
    def all_ids(self) -> List[str]:
        """Get all command IDs (primary ID + aliases)."""
        if isinstance(self.id, list):
            return self.id
        return [self.id]


class Group(BaseModel):
    """A command group/category."""

    id: str = Field(description="Group identifier")
    title: str = Field(description="Group display title")
    description: Optional[str] = Field(default=None, description="Group description")
    order: Optional[int] = Field(
        default=None, description="Sort order (lower first)"
    )
    commands: List[str] | List[Command] | List[Dict[str, Any]] = Field(
        description="List of command IDs (strings) or command definitions (objects) in this group"
    )


class ComposeProfile(BaseModel):
    """Docker Compose profile shortcut."""

    id: str = Field(description="Profile identifier")
    title: str = Field(description="Profile display title")
    description: Optional[str] = Field(default=None, description="Profile description")
    profiles: List[str] = Field(description="Docker Compose profiles to use")
    command: str = Field(
        default="up", description="Compose command (up, down, restart, etc.)"
    )
    flags: Optional[List[str]] = Field(
        default=None, description="Additional flags for compose command"
    )


class GlobalDefaults(BaseModel):
    """Global default settings."""

    docker_registry: Optional[str] = Field(
        default="registry.schwende.lan:5000", description="Default Docker registry"
    )


class ProjectEnvironments(BaseModel):
    """Project-specific environment variables."""

    dev: Optional[Dict[str, str]] = Field(
        default=None, description="Development environment variables"
    )
    test: Optional[Dict[str, str]] = Field(
        default=None, description="Test environment variables"
    )
    prod: Optional[Dict[str, str]] = Field(
        default=None, description="Production environment variables"
    )


class SindriConfig(BaseModel):
    """Main Sindri configuration schema."""

    version: Optional[str] = Field(
        default="1.0", description="Config schema version"
    )
    project_name: Optional[str] = Field(
        default=None, description="Project name override"
    )

    commands: List[Command] = Field(description="List of commands")
    groups: Optional[List[Group]] = Field(
        default=None, description="Command groups"
    )
    compose_profiles: Optional[List[ComposeProfile]] = Field(
        default=None, description="Docker Compose profiles"
    )

    # Private attributes (not part of model schema)
    _defaults: Optional[GlobalDefaults] = PrivateAttr(default=None)
    _project_envs: Optional[ProjectEnvironments] = PrivateAttr(default=None)
    _config_path: Optional[Path] = PrivateAttr(default=None)
    _workspace_dir: Optional[Path] = PrivateAttr(default=None)

    @field_validator("commands")
    @classmethod
    def validate_command_ids(cls, v: List[Command]) -> List[Command]:
        """Validate that all command IDs and aliases are unique."""
        # Helper to get primary ID from cmd.id
        def get_primary_id(cmd: Command) -> str:
            if isinstance(cmd.id, list):
                return cmd.id[0] if cmd.id else ""
            return cmd.id

        # Helper to get all IDs from cmd.id
        def get_all_ids(cmd: Command) -> List[str]:
            if isinstance(cmd.id, list):
                return cmd.id
            return [cmd.id]

        # Collect all IDs (primary IDs from id field)
        primary_ids = [get_primary_id(cmd) for cmd in v]
        if len(primary_ids) != len(set(primary_ids)):
            raise ValueError("Command primary IDs must be unique")

        # Collect all IDs (including list IDs and aliases)
        all_ids = set()
        for cmd in v:
            cmd_ids = get_all_ids(cmd)
            for cmd_id in cmd_ids:
                if cmd_id in all_ids:
                    raise ValueError(
                        f"Command ID/alias '{cmd_id}' is not unique. "
                        "All IDs and aliases must be unique."
                    )
                all_ids.add(cmd_id)

            # Also check aliases field
            if cmd.aliases:
                for alias in cmd.aliases:
                    if alias in all_ids:
                        raise ValueError(
                            f"Alias '{alias}' conflicts with command ID. "
                            "Aliases must be unique and not match any command ID."
                        )
                    all_ids.add(alias)

        # Check that aliases are unique among themselves
        all_aliases = []
        for cmd in v:
            if cmd.aliases:
                all_aliases.extend(cmd.aliases)

        if len(all_aliases) != len(set(all_aliases)):
            raise ValueError("Command aliases must be unique")

        return v

    def get_command_by_id(
        self, command_id: str, prefer_id: Optional[str] = None
    ) -> Optional[Command]:
        """
        Get a command by its ID or alias.

        Args:
            command_id: Command ID or alias
            prefer_id: If provided, prefer commands with this ID

        Returns:
            Command object or None if not found
        """
        # If prefer_id is specified, try to find that first
        if prefer_id:
            for cmd in self.commands:
                primary_id = cmd.id[0] if isinstance(cmd.id, list) else cmd.id
                if primary_id == prefer_id:
                    return cmd
        
        # Then search normally
        for cmd in self.commands:
            # Check if command_id matches any ID in the id field (string or list)
            if isinstance(cmd.id, list):
                if command_id in cmd.id:
                    return cmd
            elif cmd.id == command_id:
                return cmd

            # Also check aliases field
            if cmd.aliases and command_id in cmd.aliases:
                return cmd

        return None

    def get_commands_by_group(self, group_id: str) -> List[Command]:
        """Get all commands in a group."""
        if not self.groups:
            return []

        group = next((g for g in self.groups if g.id == group_id), None)
        if not group:
            return []

        commands = []
        for cmd_id in group.commands:
            cmd = self.get_command_by_id(cmd_id)
            if cmd:
                commands.append(cmd)
        return commands

    def get_env_vars(self, env: str = "dev") -> Dict[str, str]:
        """
        Get environment variables for a specific environment.

        Args:
            env: Environment name (dev, test, prod)

        Returns:
            Dictionary of environment variables (project-level)
        """
        if not self._project_envs:
            return {}

        env_vars: Dict[str, str] = {}

        # Get environment-specific vars
        if env == "dev" and self._project_envs.dev:
            env_vars.update(dict(self._project_envs.dev))
        elif env == "test" and self._project_envs.test:
            env_vars.update(dict(self._project_envs.test))
        elif env == "prod" and self._project_envs.prod:
            env_vars.update(dict(self._project_envs.prod))

        return env_vars

    def get_commands_organized_by_groups(
        self,
    ) -> List[tuple[Optional[Group], List[Command]]]:
        """
        Organize commands by groups.

        Returns:
            List of tuples (Group, List[Command]). If Group is None, these are ungrouped commands.
        """
        if not self.groups:
            # No groups defined, return all commands as ungrouped
            return [(None, self.commands.copy())]

        # Track which commands are in groups (use primary IDs)
        grouped_command_ids = set()
        for group in self.groups:
            # group.commands is a list of strings (command IDs)
            grouped_command_ids.update(group.commands)

        # Get ungrouped commands (check primary ID)
        ungrouped = [
            cmd for cmd in self.commands if cmd.primary_id not in grouped_command_ids
        ]

        # Sort groups by order (None last)
        sorted_groups = sorted(
            self.groups, key=lambda g: (g.order is None, g.order or 0)
        )

        # Build result list
        result: List[tuple[Optional[Group], List[Command]]] = []

        for group in sorted_groups:
            commands = []
            for cmd_id in group.commands:
                cmd = self.get_command_by_id(cmd_id)
                if cmd:
                    commands.append(cmd)
            if commands:
                result.append((group, commands))

        # Add ungrouped commands at the end
        if ungrouped:
            result.append((None, ungrouped))

        return result

