"""Helper functions to update pyproject.toml for Sindri integration."""

import re
from pathlib import Path
from typing import Optional, Tuple

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None  # type: ignore

try:
    import tomli_w  # For writing TOML
except ImportError:
    tomli_w = None  # type: ignore


def update_pyproject_for_sindri(pyproject_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Update existing pyproject.toml to add sindri dependency and script.
    
    Args:
        pyproject_path: Path to pyproject.toml
        
    Returns:
        Tuple of (success, error_message)
    """
    if not pyproject_path.exists():
        return False, "pyproject.toml not found"
    
    if tomllib is None:
        return False, "tomllib or tomli not available"
    
    try:
        # Read existing pyproject.toml
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        
        # Normalize project name if needed
        from sindri.utils.name_normalizer import normalize_project_name
        
        if "project" in data and "name" in data["project"]:
            original_name = data["project"]["name"]
            normalized_name = normalize_project_name(original_name)
            if original_name != normalized_name:
                data["project"]["name"] = normalized_name
        
        # Ensure dependencies list exists
        if "project" not in data:
            data["project"] = {}
        
        if "dependencies" not in data["project"]:
            data["project"]["dependencies"] = []
        
        # Add sindri dependency if not present
        dependencies = data["project"]["dependencies"]
        if not any(dep.startswith("sindri") for dep in dependencies if isinstance(dep, str)):
            dependencies.append("sindri")
        
        # Ensure scripts section exists
        if "scripts" not in data["project"]:
            data["project"]["scripts"] = {}
        
        # Add sindri script if not present
        if "sindri" not in data["project"]["scripts"]:
            data["project"]["scripts"]["sindri"] = "sindri.cli.main:main"
        
        # Write back to file
        # Since tomli_w might not be available, we'll use a simple string-based approach
        return _write_pyproject_toml(pyproject_path, data)
        
    except Exception as e:
        return False, f"Error updating pyproject.toml: {e}"


def _write_pyproject_toml(pyproject_path: Path, data: dict) -> Tuple[bool, Optional[str]]:
    """
    Write pyproject.toml using tomli_w if available, otherwise use simple string formatting.
    
    Args:
        pyproject_path: Path to pyproject.toml
        data: TOML data dictionary
        
    Returns:
        Tuple of (success, error_message)
    """
    if tomli_w is not None:
        try:
            with pyproject_path.open("wb") as f:
                tomli_w.dump(data, f)
            return True, None
        except Exception as e:
            return False, f"Error writing pyproject.toml: {e}"
    else:
        # Fallback: read original file and update it manually
        try:
            content = pyproject_path.read_text(encoding="utf-8")
            updated_content = _update_pyproject_content(content, data)
            pyproject_path.write_text(updated_content, encoding="utf-8")
            return True, None
        except Exception as e:
            return False, f"Error writing pyproject.toml: {e}"


def _update_pyproject_content(content: str, data: dict) -> str:
    """
    Update pyproject.toml content by appending missing sections and normalizing project name.
    This is a simplified fallback when tomli_w is not available.
    """
    import re
    
    # Check what needs to be added
    project_data = data.get("project", {})
    dependencies = project_data.get("dependencies", [])
    scripts = project_data.get("scripts", {})
    normalized_name = project_data.get("name", "")
    
    has_sindri_dep = any("sindri" in str(dep).lower() for dep in dependencies)
    has_sindri_script = "sindri" in scripts
    
    lines = content.split("\n")
    result = []
    
    # Find [project] section and update name
    project_idx = -1
    scripts_idx = -1
    dependencies_idx = -1
    name_updated = False
    
    for i, line in enumerate(lines):
        if line.strip() == "[project]":
            project_idx = i
            result.append(line)
        elif line.strip() == "[project.scripts]":
            scripts_idx = i
            result.append(line)
        elif line.strip().startswith("dependencies") and project_idx >= 0:
            dependencies_idx = i
            result.append(line)
        elif project_idx >= 0 and not name_updated and line.strip().startswith("name"):
            # Update project name
            # Match: name = "hexSwitch" or name = "hexSwitch"
            match = re.match(r'(name\s*=\s*)(["\']?)([^"\'\n]+)(["\']?)', line)
            if match and normalized_name:
                prefix = match.group(1)
                quote1 = match.group(2) or '"'
                quote2 = match.group(4) or '"'
                result.append(f'{prefix}{quote1}{normalized_name}{quote2}')
                name_updated = True
            else:
                result.append(line)
        else:
            result.append(line)
    
    # If name wasn't updated but should be, find and update it
    if not name_updated and normalized_name and project_idx >= 0:
        # Search for name line in project section
        search_end = scripts_idx if scripts_idx >= 0 else len(result)
        for i in range(project_idx + 1, search_end):
            if i < len(result) and result[i].strip().startswith("name"):
                match = re.match(r'(name\s*=\s*)(["\']?)([^"\'\n]+)(["\']?)', result[i])
                if match:
                    prefix = match.group(1)
                    quote1 = match.group(2) or '"'
                    quote2 = match.group(4) or '"'
                    result[i] = f'{prefix}{quote1}{normalized_name}{quote2}'
                    name_updated = True
                    break
    
    # Check if content already has sindri dependency
    content_lower = "\n".join(result).lower()
    
    # Add sindri dependency if needed
    if not has_sindri_dep and project_idx >= 0 and "sindri" not in content_lower:
        if dependencies_idx >= 0:
            # Dependencies section exists, find closing bracket
            for i in range(dependencies_idx + 1, len(result)):
                if result[i].strip() == "]":
                    indent = " " * max(4, len(result[i]) - len(result[i].lstrip()))
                    result.insert(i, f'{indent}"sindri",')
                    break
        else:
            # No dependencies section, add it after [project]
            insert_pos = project_idx + 1
            # Find end of project section (next [section] or end of file)
            for i in range(project_idx + 1, len(result)):
                if result[i].strip().startswith("["):
                    insert_pos = i
                    break
            result.insert(insert_pos, 'dependencies = [')
            result.insert(insert_pos + 1, '    "sindri",')
            result.insert(insert_pos + 2, ']')
    
    # Add sindri script if needed
    if not has_sindri_script and "[project.scripts]" not in content_lower:
        if scripts_idx >= 0:
            # Scripts section exists, append sindri
            result.insert(scripts_idx + 1, 'sindri = "sindri.cli:app"')
        elif project_idx >= 0:
            # No scripts section, add it after project section
            insert_pos = project_idx + 1
            # Find end of project section
            for i in range(project_idx + 1, len(result)):
                if result[i].strip().startswith("["):
                    insert_pos = i
                    break
            result.insert(insert_pos, "")
            result.insert(insert_pos + 1, "[project.scripts]")
            result.insert(insert_pos + 2, 'sindri = "sindri.cli:app"')
    
    return "\n".join(result)


def add_sindri_config_to_pyproject(
    pyproject_path: Path, sindri_config: dict
) -> Tuple[bool, Optional[str]]:
    """
    Add or update [tool.sindri] section in pyproject.toml.
    
    Args:
        pyproject_path: Path to pyproject.toml
        sindri_config: Dictionary with sindri configuration (will be placed under [tool.sindri])
        
    Returns:
        Tuple of (success, error_message)
    """
    if not pyproject_path.exists():
        return False, "pyproject.toml not found"
    
    if tomllib is None:
        return False, "tomllib or tomli not available"
    
    try:
        # Read existing pyproject.toml
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        
        # Add or update [tool.sindri] section
        if "tool" not in data:
            data["tool"] = {}
        data["tool"]["sindri"] = sindri_config
        
        # Write back using tomli_w if available, otherwise use string manipulation
        if tomli_w is not None:
            with pyproject_path.open("wb") as f:
                tomli_w.dump(data, f)
            return True, None
        else:
            # Fallback: append [tool.sindri] section
            content = pyproject_path.read_text(encoding="utf-8")
            updated_content = _append_tool_sindri_section(content, sindri_config)
            pyproject_path.write_text(updated_content, encoding="utf-8")
            return True, None
        
    except Exception as e:
        return False, f"Error updating pyproject.toml: {e}"


def _append_tool_sindri_section(content: str, sindri_config: dict) -> str:
    """
    Append [tool.sindri] section to pyproject.toml content.
    If [tool.sindri] already exists, replace it.
    """
    import re
    
    lines = content.split("\n")
    result = []
    tool_sindri_start = -1
    tool_sindri_end = -1
    in_tool_sindri = False
    indent_level = 0
    
    # Find existing [tool.sindri] section
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "[tool.sindri]":
            tool_sindri_start = i
            in_tool_sindri = True
            indent_level = len(line) - len(line.lstrip())
            result.append(line)
        elif in_tool_sindri:
            # Check if we've left the [tool.sindri] section
            if stripped.startswith("[") and not stripped.startswith("[tool.sindri"):
                tool_sindri_end = i
                in_tool_sindri = False
                result.append(line)
            elif stripped == "" and i > tool_sindri_start + 1:
                # Empty line might indicate end of section
                tool_sindri_end = i
                in_tool_sindri = False
                result.append(line)
            elif not in_tool_sindri:
                result.append(line)
            # Skip lines inside [tool.sindri] (we'll replace them)
        else:
            result.append(line)
    
    # Generate [tool.sindri] section content
    sindri_lines = ["[tool.sindri]"]
    for key, value in sindri_config.items():
        if isinstance(value, list):
            sindri_lines.append(f'{key} = {value}')
        elif isinstance(value, str):
            sindri_lines.append(f'{key} = "{value}"')
        else:
            sindri_lines.append(f'{key} = {value}')
    
    # Replace or append [tool.sindri] section
    if tool_sindri_start >= 0:
        # Replace existing section
        if tool_sindri_end > tool_sindri_start:
            # Remove old section
            result = result[:tool_sindri_start] + result[tool_sindri_end:]
        else:
            # Section goes to end of file
            result = result[:tool_sindri_start]
        # Insert new section
        result.extend(sindri_lines)
    else:
        # Append new section at end
        if result and result[-1].strip() != "":
            result.append("")
        result.extend(sindri_lines)
    
    return "\n".join(result)
