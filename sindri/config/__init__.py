"""Configuration discovery and schema for Sindri."""

from sindri.config.models import (
    Command,
    CommandDependency,
    ComposeProfile,
    GlobalDefaults,
    Group,
    ProjectEnvironments,
    SindriConfig,
)
from sindri.config.loader import (
    discover_config,
    get_config_dir,
    load_config,
    load_global_defaults,
    load_project_environments,
)

__all__ = [
    "Command",
    "CommandDependency",
    "ComposeProfile",
    "GlobalDefaults",
    "Group",
    "ProjectEnvironments",
    "SindriConfig",
    "discover_config",
    "get_config_dir",
    "load_config",
    "load_global_defaults",
    "load_project_environments",
]

