"""Helper functions to validate dependencies in pyproject.toml."""

from pathlib import Path
from typing import List, Optional, Tuple

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None  # type: ignore


def validate_pyproject_dependencies(pyproject_path: Path) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate dependencies in pyproject.toml.
    
    Args:
        pyproject_path: Path to pyproject.toml
        
    Returns:
        Tuple of (is_valid, error_message, invalid_deps)
    """
    if not pyproject_path.exists():
        return False, "pyproject.toml not found", []
    
    if tomllib is None:
        return True, None, []  # Can't validate without tomllib
    
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        
        invalid_deps = []
        
        # Check project.dependencies
        if "project" in data and "dependencies" in data["project"]:
            deps = data["project"]["dependencies"]
            for dep in deps:
                if isinstance(dep, str):
                    # Check for common invalid patterns
                    if dep.startswith("http://") or dep.startswith("https://"):
                        # URL dependencies should have @ separator
                        if "@" not in dep:
                            invalid_deps.append(dep)
                    elif " " in dep and ("http://" in dep or "https://" in dep):
                        # Space in URL dependency
                        invalid_deps.append(dep)
        
        # Check project.optional-dependencies
        if "project" in data and "optional-dependencies" in data["project"]:
            for group_name, group_deps in data["project"]["optional-dependencies"].items():
                for dep in group_deps:
                    if isinstance(dep, str):
                        if dep.startswith("http://") or dep.startswith("https://"):
                            if "@" not in dep:
                                invalid_deps.append(dep)
                        elif " " in dep and ("http://" in dep or "https://" in dep):
                            invalid_deps.append(dep)
        
        if invalid_deps:
            error_msg = (
                f"Invalid dependency URLs found in pyproject.toml:\n"
                + "\n".join(f"  - {dep}" for dep in invalid_deps)
                + "\n\n"
                + "URL dependencies should be in format:\n"
                + "  package-name @ https://url\n"
                + "  or\n"
                + "  package-name @ git+https://url"
            )
            return False, error_msg, invalid_deps
        
        return True, None, []
        
    except Exception as e:
        return False, f"Error parsing pyproject.toml: {e}", []

