"""Configuration loading and discovery."""

from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None  # type: ignore

from sindri.config.implemented_commands import (
    convert_to_config_command,
    get_implemented_commands,
)

from sindri.config.models import (
    GlobalDefaults,
    ProjectEnvironments,
    SindriConfig,
)

# Version command IDs that should always be available
VERSION_COMMAND_IDS = ["version show", "version bump", "version tag"]


def discover_config(
    start_path: Optional[Path] = None, config_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Discover the Sindri config file by searching upwards from start_path.
    
    Priority order:
    1. Explicit config_path (if provided)
    2. pyproject.toml with [tool.sindri] section
    3. .sindri/sindri.toml
    4. sindri.toml in root

    Args:
        start_path: Starting directory (defaults to current working directory)
        config_path: Override path to config file (if provided, returns this)

    Returns:
        Path to config file or None if not found
    """
    if config_path:
        path = Path(config_path).resolve()
        if path.exists():
            return path
        return None

    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    current = start_path

    # Stop at filesystem root
    while current != current.parent:
        # First check for pyproject.toml with [tool.sindri] section
        pyproject_path = current / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    if "tool" in data and "sindri" in data["tool"]:
                        return pyproject_path
            except Exception:
                # If we can't read or parse, continue searching
                pass
        
        # Then check in .sindri/ directory
        sindri_dir = current / ".sindri"
        if sindri_dir.exists() and sindri_dir.is_dir():
            config_file = sindri_dir / "sindri.toml"
            if config_file.exists():
                return config_file
        
        # Finally check sindri.toml in current directory
        config_file = current / "sindri.toml"
        if config_file.exists():
            return config_file
            
        current = current.parent

    return None


def load_global_defaults() -> GlobalDefaults:
    """Load global defaults from ~/.sindri/config.toml."""
    home = Path.home()
    global_config = home / ".sindri" / "config.toml"

    if not global_config.exists():
        # Return defaults
        return GlobalDefaults()

    try:
        with open(global_config, "rb") as f:
            data = tomllib.load(f)

        defaults_data = data.get("defaults", {})
        return GlobalDefaults(**defaults_data)
    except Exception:
        # If loading fails, return defaults
        return GlobalDefaults()


def load_project_environments(workspace_dir: Path) -> ProjectEnvironments:
    """Load project-specific environments from <workspace_dir>/.sindri/config.toml."""
    project_config = workspace_dir / ".sindri" / "config.toml"

    if not project_config.exists():
        # Return empty environments
        return ProjectEnvironments()

    try:
        with open(project_config, "rb") as f:
            data = tomllib.load(f)

        envs_data = data.get("environments", {})
        return ProjectEnvironments(**envs_data)
    except Exception:
        # If loading fails, return empty environments
        return ProjectEnvironments()


def load_config(
    config_path: Optional[Path] = None, start_path: Optional[Path] = None
) -> SindriConfig:
    """
    Load and validate a Sindri configuration file.

    Args:
        config_path: Override path to config file
        start_path: Starting directory for discovery (if config_path not provided)

    Returns:
        Validated SindriConfig instance

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid
    """
    path = discover_config(start_path, config_path)
    if not path:
        raise FileNotFoundError(
            "No Sindri config file found. Run 'sindri init' to create one."
        )

    if path.suffix == ".toml" or path.name.endswith(".toml"):
        # Load TOML
        with open(path, "rb") as f:
            try:
                full_data = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise ValueError(f"Invalid TOML in config file: {e}") from e
        
        # Check if file is empty
        if not full_data:
            raise ValueError("Config file is empty or invalid")
        
        # Extract sindri config from pyproject.toml or use full data
        if path.name == "pyproject.toml" and "tool" in full_data and "sindri" in full_data["tool"]:
            # Extract [tool.sindri] section
            data = full_data["tool"]["sindri"]
            # Workspace is the directory containing pyproject.toml (project root)
            workspace_dir = path.parent
        else:
            # Standalone sindri.toml file
            data = full_data
            # Workspace is the directory containing sindri.toml
            workspace_dir = path.parent
    else:
        # For now, only TOML is supported
        # YAML support could be added later
        raise ValueError(f"Unsupported config format: {path.suffix}")

    # Load global defaults
    defaults = load_global_defaults()

    # Load project environments
    project_envs = load_project_environments(workspace_dir)

    # Get groups configuration first to know which groups to load
    groups_config = data.get("groups", [])
    
    # Determine which groups to load
    if isinstance(groups_config, list) and groups_config and isinstance(groups_config[0], str):
        # Simple reference list - only load these groups
        group_ids_to_load = groups_config
    elif isinstance(groups_config, list) and groups_config:
        # Traditional groups definition - need to load all to check references
        group_ids_to_load = None
    else:
        # No groups defined - don't load any implemented commands
        group_ids_to_load = []
    
    # Get implemented commands from Python classes (only configured groups)
    # Always include version and sindri group commands
    if group_ids_to_load is not None:
        if "version" not in group_ids_to_load:
            group_ids_to_load = list(group_ids_to_load) + ["version"]
        if "sindri" not in group_ids_to_load:
            group_ids_to_load = list(group_ids_to_load) + ["sindri"]
        implemented_commands = get_implemented_commands(group_ids_to_load)
    else:
        # Load all groups (which includes version and sindri)
        implemented_commands = get_implemented_commands(None)
    
    all_commands = data.get("commands", [])
    processed_groups = []
    referenced_command_ids = set()
    
    # Always add version group commands to all_commands if not already present
    always_available_commands = VERSION_COMMAND_IDS
    for cmd_id in always_available_commands:
        if cmd_id in implemented_commands:
            # Check if already in all_commands
            existing = False
            for existing_cmd in all_commands:
                existing_id = existing_cmd.get("id")
                existing_primary = existing_id[0] if isinstance(existing_id, list) else existing_id
                if existing_primary == cmd_id:
                    existing = True
                    break
            if not existing:
                impl_cmd = implemented_commands[cmd_id]
                config_cmd = convert_to_config_command(impl_cmd)
                all_commands.append(config_cmd.model_dump())
                referenced_command_ids.add(cmd_id)

    # Check if groups is a simple list of group IDs
    if isinstance(groups_config, list) and groups_config and isinstance(groups_config[0], str):
        # Simple reference list: groups = ["general", "application", ...]
        from sindri.commands import (
            ApplicationGroup,
            ComposeGroup,
            DockerGroup,
            GeneralGroup,
            GitGroup,
            PyPIGroup,
            QualityGroup,
            SindriGroup,
        )

        # Core groups (always available)
        core_group_classes = {
            "sindri": SindriGroup,
            "general": GeneralGroup,
            "quality": QualityGroup,
            "application": ApplicationGroup,
        }
        
        # Optional groups (may not be available if extras not installed)
        optional_group_classes = {
            "docker": DockerGroup,
            "compose": ComposeGroup,
            "git": GitGroup,
            "pypi": PyPIGroup,
        }
        
        # Combine for lookup
        group_classes = {**core_group_classes, **optional_group_classes}

        # Create groups from references
        for group_id in groups_config:
            if group_id in group_classes:
                group_class = group_classes[group_id]
                try:
                    group_instance = group_class()
                except (ImportError, AttributeError, TypeError):
                    # Optional group not available (graceful degradation)
                    continue
                
                # Get all commands from this group
                group_commands = group_instance.get_commands()
                group_command_ids = []
                
                for cmd in group_commands:
                    cmd_id = cmd.command_id
                    group_command_ids.append(cmd_id)
                    
                    # Convert to ConfigCommand if not already in all_commands
                    if cmd_id not in referenced_command_ids:
                        config_cmd = convert_to_config_command(cmd)
                        all_commands.append(config_cmd.model_dump())
                        referenced_command_ids.add(cmd_id)
                
                # Create group entry
                processed_groups.append({
                    "id": group_id,
                    "title": group_instance.title,
                    "description": group_instance.description,
                    "order": group_instance.order,
                    "commands": group_command_ids,
                })
    else:
        # Traditional groups definition with inline commands
        groups_data = groups_config if isinstance(groups_config, list) else []
        
        for group_data in groups_data:
            group_commands = group_data.get("commands", [])
            processed_group_commands = []

            for cmd_item in group_commands:
                if isinstance(cmd_item, dict):
                    # Inline command definition - add to all_commands
                    all_commands.append(cmd_item)
                    # Store primary ID for reference
                    cmd_id_val = cmd_item.get("id")
                    if isinstance(cmd_id_val, list):
                        primary_id = cmd_id_val[0]
                    else:
                        primary_id = cmd_id_val
                    processed_group_commands.append(primary_id)
                    referenced_command_ids.add(primary_id)
                else:
                    # String reference - check if it's an implemented command
                    cmd_ref_id = str(cmd_item)
                    cmd_dict = None
                    if cmd_ref_id in implemented_commands:
                        # Convert implemented command to ConfigCommand dict
                        impl_cmd = implemented_commands[cmd_ref_id]
                        config_cmd = convert_to_config_command(impl_cmd)
                        # Add to all_commands if not already there
                        cmd_dict = config_cmd.model_dump()
                    
                    # Check if already exists (compare primary IDs)
                    if cmd_dict is not None:
                        existing = False
                        primary_id = cmd_ref_id  # cmd_ref_id is the primary ID
                        for existing_cmd in all_commands:
                            existing_id = existing_cmd.get("id")
                            existing_primary = (
                                existing_id[0]
                                if isinstance(existing_id, list)
                                else existing_id
                            )
                            if existing_primary == primary_id:
                                existing = True
                                break
                        if not existing:
                            all_commands.append(cmd_dict)
                        referenced_command_ids.add(cmd_ref_id)
                    processed_group_commands.append(cmd_ref_id)

            # Update group with processed commands (as strings)
            group_data["commands"] = processed_group_commands
            processed_groups.append(group_data)

    # Always ensure version and sindri groups exist
    version_group_exists = any(g.get("id") == "version" for g in processed_groups)
    sindri_group_exists = any(g.get("id") == "sindri" for g in processed_groups)
    
    if not version_group_exists:
        # Add version group
        processed_groups.append({
            "id": "version",
            "title": "Version",
            "description": "Version management commands",
            "order": 2,
            "commands": VERSION_COMMAND_IDS,
        })
    
    if not sindri_group_exists:
        # Add sindri group (empty, use 'sindri init' instead)
        processed_groups.append({
            "id": "sindri",
            "title": "Sindri",
            "description": "Sindri project setup and initialization",
            "order": 0,
            "commands": [],
        })
    
    # Update data with processed groups
    data["commands"] = all_commands
    # Only set groups if we have any, otherwise leave it as None
    if processed_groups:
        data["groups"] = processed_groups
    elif "groups" not in data:
        # If groups wasn't in original data, don't add it (will be None)
        pass
    else:
        # If groups was in original data but is now empty, set to None
        # (SindriConfig expects Optional[List[Group]], so None is valid)
        if not processed_groups:
            data["groups"] = None
        else:
            data["groups"] = processed_groups

    # Validate and create config
    config = SindriConfig(**data)

    # Store defaults, project environments, and config file path
    config._defaults = defaults  # type: ignore
    config._project_envs = project_envs  # type: ignore
    config._config_path = path  # type: ignore
    config._workspace_dir = workspace_dir  # type: ignore

    return config


def get_config_dir(config: SindriConfig) -> Path:
    """
    Get the project root directory.

    If config is in .sindri/sindri.toml, returns parent (project root).
    If config is in pyproject.toml, returns the directory containing pyproject.toml.
    Otherwise returns the directory containing the config file.
    """
    config_path = config._config_path  # type: ignore
    if config_path is None:
        raise ValueError("Config path is not set")
    config_dir = config_path.parent

    # If config is in .sindri/, use parent (project root)
    if config_dir.name == ".sindri":
        return config_dir.parent

    # Otherwise, config_dir is already the project root
    return config_dir

