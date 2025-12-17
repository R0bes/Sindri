"""Utility functions for Sindri."""

import os
import platform
from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None  # type: ignore


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the project root by searching upwards for common markers.
    
    Args:
        start_path: Starting directory (defaults to current working directory)
        
    Returns:
        Path to project root or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    current = start_path
    
    # Stop at filesystem root
    while current != current.parent:
        # Check for common project markers
        if any((current / marker).exists() for marker in [".git", ".hg", ".svn", "pyproject.toml", "setup.py"]):
            return current
        current = current.parent
    
    return None


def get_shell() -> str:
    """
    Get the appropriate shell command for the current platform.
    
    Returns:
        Shell command string
    """
    if platform.system() == "Windows":
        return os.environ.get("COMSPEC", "cmd.exe")
    else:
        return os.environ.get("SHELL", "/bin/sh")


def escape_shell_arg(arg: str) -> str:
    """
    Escape a shell argument for safe execution.
    
    Args:
        arg: Argument to escape
        
    Returns:
        Escaped argument
    """
    if platform.system() == "Windows":
        # Windows cmd.exe escaping
        return arg.replace('"', '""')
    else:
        # Unix shell escaping
        return arg.replace("'", "'\"'\"'")


def get_project_name_from_pyproject(start_path: Optional[Path] = None) -> Optional[str]:
    """
    Get project name from pyproject.toml.
    
    Args:
        start_path: Starting directory to search from (defaults to current working directory)
        
    Returns:
        Project name from pyproject.toml or None if not found
    """
    if tomllib is None:
        return None
    
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    # Search upwards for pyproject.toml
    current = start_path
    while current != current.parent:
        pyproject_path = current / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with pyproject_path.open("rb") as f:
                    data = tomllib.load(f)
                    # Get project name from [project] section
                    if "project" in data and "name" in data["project"]:
                        return data["project"]["name"]
            except (OSError, KeyError, ValueError):
                # If we can't read or parse the file, continue searching
                pass
        current = current.parent
    
    return None


def get_project_version_from_pyproject(start_path: Optional[Path] = None) -> Optional[str]:
    """
    Get project version from pyproject.toml.
    
    Args:
        start_path: Starting directory to search from (defaults to current working directory)
        
    Returns:
        Project version from pyproject.toml or None if not found
    """
    if tomllib is None:
        return None
    
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    # Search upwards for pyproject.toml
    current = start_path
    while current != current.parent:
        pyproject_path = current / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with pyproject_path.open("rb") as f:
                    data = tomllib.load(f)
                    # Get project version from [project] section
                    if "project" in data and "version" in data["project"]:
                        return data["project"]["version"]
            except (OSError, KeyError, ValueError):
                # If we can't read or parse the file, continue searching
                pass
        current = current.parent
    
    return None


def get_project_name(cwd: Path) -> str:
    """
    Get a project name, first trying pyproject.toml, then falling back to directory name.
    
    Args:
        cwd: Current working directory
        
    Returns:
        Project name from pyproject.toml, directory name, or "unknown"
    """
    # First try to get from pyproject.toml
    project_name = get_project_name_from_pyproject(cwd)
    if project_name:
        return project_name
    
    # Fallback to directory name
    root = find_project_root(cwd)
    if root:
        return root.name
    return cwd.name or "unknown"

