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

from sindri.config.models import (
    GlobalDefaults,
    ProjectEnvironments,
    SindriConfig,
)


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
        
        # Then check .sindri.toml in current directory
        sindri_dot_toml = current / ".sindri.toml"
        if sindri_dot_toml.exists():
            return sindri_dot_toml
        
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
        return GlobalDefaults()

    try:
        with open(global_config, "rb") as f:
            data = tomllib.load(f)

        defaults_data = data.get("defaults", {})
        return GlobalDefaults(**defaults_data)
    except Exception:
        return GlobalDefaults()


def load_project_environments(workspace_dir: Path) -> ProjectEnvironments:
    """Load project-specific environments from <workspace_dir>/.sindri/config.toml."""
    project_config = workspace_dir / ".sindri" / "config.toml"

    if not project_config.exists():
        return ProjectEnvironments()

    try:
        with open(project_config, "rb") as f:
            data = tomllib.load(f)

        envs_data = data.get("environments", {})
        return ProjectEnvironments(**envs_data)
    except Exception:
        return ProjectEnvironments()


def load_config(
    config_path: Optional[Path] = None, start_path: Optional[Path] = None
) -> SindriConfig:
    """
    Load and validate a Sindri configuration file.
    
    This function only loads the TOML configuration. Command registration
    from built-in groups is handled by the Registry (sindri.core.registry).

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
        with open(path, "rb") as f:
            try:
                full_data = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise ValueError(f"Invalid TOML in config file: {e}") from e
        
        if not full_data:
            raise ValueError("Config file is empty or invalid")
        
        # Extract sindri config from pyproject.toml or use full data
        if path.name == "pyproject.toml" and "tool" in full_data and "sindri" in full_data["tool"]:
            data = full_data["tool"]["sindri"]
            workspace_dir = path.parent
        else:
            data = full_data
            workspace_dir = path.parent
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}")

    # Load global defaults
    defaults = load_global_defaults()

    # Load project environments
    project_envs = load_project_environments(workspace_dir)

    # Process groups configuration
    groups_config = data.get("groups", [])
    
    # If groups is a simple list of group IDs (references), expand them
    if isinstance(groups_config, list) and groups_config and isinstance(groups_config[0], str):
        # Simple reference list: groups = ["general", "docker", ...]
        # The Registry will handle loading commands from these groups
        # We just need to create group metadata entries
        processed_groups = []
        for group_id in groups_config:
            processed_groups.append({
                "id": group_id,
                "title": group_id.title(),
                "description": f"{group_id.title()} commands",
                "commands": [],  # Commands will be loaded by Registry
            })
            data["groups"] = processed_groups
    
    # Ensure commands list exists
    if "commands" not in data:
        data["commands"] = []

    # Validate and create config
    config = SindriConfig(**data)

    # Store metadata
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

    return config_dir
