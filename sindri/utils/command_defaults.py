"""Helper functions to determine intelligent command defaults."""

import subprocess
from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None  # type: ignore


def detect_linter(cwd: Path) -> Optional[str]:
    """
    Detect which linter is available and configured.
    
    Args:
        cwd: Current working directory
        
    Returns:
        Linter command or None if not found
    """
    # Check for ruff (most common modern linter)
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            timeout=2,
            cwd=cwd,
        )
        if result.returncode == 0:
            # Check if pyproject.toml has ruff config
            pyproject = cwd / "pyproject.toml"
            if pyproject.exists() and tomllib:
                try:
                    with pyproject.open("rb") as f:
                        data = tomllib.load(f)
                        if "tool" in data and "ruff" in data["tool"]:
                            return "ruff check ."
                except Exception:
                    pass
            return "ruff check ."
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check for flake8
    try:
        result = subprocess.run(
            ["flake8", "--version"],
            capture_output=True,
            timeout=2,
            cwd=cwd,
        )
        if result.returncode == 0:
            return "flake8 ."
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check for pylint
    try:
        result = subprocess.run(
            ["pylint", "--version"],
            capture_output=True,
            timeout=2,
            cwd=cwd,
        )
        if result.returncode == 0:
            return "pylint ."
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def detect_validator(cwd: Path) -> Optional[str]:
    """
    Detect which validator is available and configured.
    
    Args:
        cwd: Current working directory
        
    Returns:
        Validator command or None if not found
    """
    # Check for mypy (most common type checker)
    try:
        result = subprocess.run(
            ["mypy", "--version"],
            capture_output=True,
            timeout=2,
            cwd=cwd,
        )
        if result.returncode == 0:
            # Check if pyproject.toml has mypy config
            pyproject = cwd / "pyproject.toml"
            if pyproject.exists() and tomllib:
                try:
                    with pyproject.open("rb") as f:
                        data = tomllib.load(f)
                        if "tool" in data and "mypy" in data["tool"]:
                            # Try to find source directory
                            if "tool" in data and "hatchling" in data.get("build-system", {}).get("build-backend", ""):
                                # Check for package name
                                if "project" in data and "name" in data["project"]:
                                    package_name = data["project"]["name"].replace("-", "_")
                                    return f"mypy {package_name}"
                            return "mypy ."
                except Exception:
                    pass
            return "mypy ."
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check for pyright
    try:
        result = subprocess.run(
            ["pyright", "--version"],
            capture_output=True,
            timeout=2,
            cwd=cwd,
        )
        if result.returncode == 0:
            return "pyright ."
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def detect_application_entry_point(cwd: Path) -> Optional[str]:
    """
    Detect application entry point.
    
    Args:
        cwd: Current working directory
        
    Returns:
        Command to start application or None if not found
    """
    # Check pyproject.toml for scripts
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists() and tomllib:
        try:
            with pyproject.open("rb") as f:
                data = tomllib.load(f)
                # Check for [project.scripts]
                if "project" in data and "scripts" in data["project"]:
                    scripts = data["project"]["scripts"]
                    if scripts:
                        # Get first script name
                        script_name = list(scripts.keys())[0]
                        return script_name
        except Exception:
            pass
    
    # Check for common entry points
    if (cwd / "main.py").exists():
        return "python main.py"
    
    if (cwd / "app.py").exists():
        return "python app.py"
    
    # Check for package structure
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists() and tomllib:
        try:
            with pyproject.open("rb") as f:
                data = tomllib.load(f)
                if "project" in data and "name" in data["project"]:
                    package_name = data["project"]["name"].replace("-", "_")
                    # Check if package directory exists
                    if (cwd / package_name / "__main__.py").exists():
                        return f"python -m {package_name}"
                    elif (cwd / package_name / "main.py").exists():
                        return f"python -m {package_name}.main"
        except Exception:
            pass
    
    return None


def get_lint_command(cwd: Path) -> str:
    """Get lint command with intelligent defaults."""
    detected = detect_linter(cwd)
    if detected:
        return detected
    return "echo 'No linter found. Install ruff, flake8, or pylint.'"


def get_validate_command(cwd: Path) -> str:
    """Get validate command with intelligent defaults."""
    detected = detect_validator(cwd)
    if detected:
        return detected
    
    # Try combined validation: check if both lint and type check are available
    lint_cmd = detect_linter(cwd)
    validator_cmd = detect_validator(cwd)
    
    if lint_cmd and validator_cmd:
        return f"{lint_cmd} && {validator_cmd}"
    elif lint_cmd:
        return lint_cmd
    elif validator_cmd:
        return validator_cmd
    
    return "echo 'No validator found. Install mypy or pyright.'"


def get_start_command(cwd: Path) -> str:
    """Get start command with intelligent defaults."""
    detected = detect_application_entry_point(cwd)
    if detected:
        return detected
    return "echo 'No application entry point found. Define start command in sindri.toml.'"


def get_stop_command(cwd: Path, start_cmd: Optional[str] = None) -> str:
    """Get stop command with intelligent defaults."""
    if start_cmd:
        # Extract process pattern from start command
        if "python -m" in start_cmd:
            module = start_cmd.split("python -m")[-1].strip()
            return f"pkill -f 'python -m {module}' || echo 'No process running'"
        elif "python" in start_cmd and ".py" in start_cmd:
            script = start_cmd.split("python")[-1].strip()
            return f"pkill -f 'python.*{script}' || echo 'No process running'"
        elif " " in start_cmd:
            # Assume it's a script name
            script_name = start_cmd.split()[0]
            return f"pkill -f '{script_name}' || echo 'No process running'"
    
    return "echo 'No stop command configured. Define stop command in sindri.toml.'"


def get_restart_command(cwd: Path, start_cmd: Optional[str] = None, stop_cmd: Optional[str] = None) -> str:
    """Get restart command with intelligent defaults."""
    if stop_cmd and start_cmd:
        # Remove echo from stop command
        stop = stop_cmd.replace(" || echo 'No process running'", "").replace(" || true", "")
        return f"{stop} || true; sleep 1; {start_cmd} &"
    elif start_cmd:
        return f"{get_stop_command(cwd, start_cmd)} || true; sleep 1; {start_cmd} &"
    
    return "echo 'No restart command configured. Define restart command in sindri.toml.'"


def get_build_command(cwd: Path) -> str:
    """Get build command with intelligent defaults."""
    # Check for common build systems
    if (cwd / "pyproject.toml").exists():
        return "pip install -e ."
    elif (cwd / "setup.py").exists():
        return "pip install -e ."
    elif (cwd / "package.json").exists():
        return "npm run build"
    elif (cwd / "Makefile").exists():
        return "make build"
    
    return "echo 'No build system detected. Define build command in sindri.toml.'"

