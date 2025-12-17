"""Helper functions for virtual environment management."""

import os
from pathlib import Path
from typing import Optional


def get_sindri_venv_path(cwd: Path) -> Path:
    """
    Get the path to the Sindri virtual environment.
    
    Args:
        cwd: Current working directory
        
    Returns:
        Path to .sindri/venv
    """
    return cwd / ".sindri" / "venv"


def get_venv_python(cwd: Path) -> Optional[str]:
    """
    Get the Python executable path in the Sindri venv.
    
    Args:
        cwd: Current working directory
        
    Returns:
        Path to Python executable or None if venv doesn't exist
    """
    venv_path = get_sindri_venv_path(cwd)
    
    if os.name == "nt":  # Windows
        python_path = venv_path / "Scripts" / "python.exe"
    else:  # Unix
        python_path = venv_path / "bin" / "python"
    
    if python_path.exists():
        return str(python_path)
    return None


def get_venv_pip(cwd: Path) -> Optional[str]:
    """
    Get the pip executable path in the Sindri venv.
    
    Args:
        cwd: Current working directory
        
    Returns:
        Path to pip executable or None if venv doesn't exist
    """
    venv_path = get_sindri_venv_path(cwd)
    
    if os.name == "nt":  # Windows
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:  # Unix
        pip_path = venv_path / "bin" / "pip"
    
    if pip_path.exists():
        return str(pip_path)
    return None


def get_setup_command(cwd: Path) -> str:
    """
    Get setup command that creates venv and installs project.
    
    Args:
        cwd: Current working directory (project root)
        
    Returns:
        Setup command string (works on both Linux and Windows)
    """
    import os
    
    # Use Python's venv module which is platform-independent
    # The venv will be created in .sindri/venv
    # Use python -m pip for better compatibility across platforms
    if os.name == "nt":  # Windows
        return (
            "if not exist .sindri mkdir .sindri && "
            "python -m venv .sindri\\venv && "
            "(.sindri\\venv\\Scripts\\python.exe -m pip install -e . 2>nul || "
            "python -m pip install -e .)"
        )
    else:  # Unix
        return (
            "mkdir -p .sindri && "
            "python -m venv .sindri/venv && "
            "(.sindri/venv/bin/python -m pip install -e . 2>/dev/null || "
            "python -m pip install -e .)"
        )


def get_install_command(cwd: Path) -> str:
    """
    Get install command that installs dependencies in venv.
    
    Args:
        cwd: Current working directory
        
    Returns:
        Install command string
    """
    python_path = get_venv_python(cwd)
    
    if python_path:
        # Venv exists, use it with python -m pip for better compatibility
        if (cwd / "requirements.txt").exists():
            return f"{python_path} -m pip install -r requirements.txt"
        elif (cwd / "pyproject.toml").exists():
            return f"{python_path} -m pip install -e ."
        else:
            return f"{python_path} -m pip install -e ."
    else:
        # No venv, create it first
        return get_setup_command(cwd)

