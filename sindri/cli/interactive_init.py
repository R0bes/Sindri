"""Interactive initialization for Sindri config."""

import os
from pathlib import Path
from typing import List, Set

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from sindri.cli.display import console
from sindri.cli.template import get_default_config_template

# Available command groups
AVAILABLE_GROUPS = {
    "general": {
        "title": "General",
        "description": "Setup and installation commands",
        "commands": ["setup", "install"],
    },
    "quality": {
        "title": "Quality",
        "description": "Code quality commands (test, lint, validate)",
        "commands": ["test", "cov", "lint", "validate"],
    },
    "application": {
        "title": "Application",
        "description": "Application lifecycle commands",
        "commands": ["start", "stop", "restart", "build"],
    },
    "docker": {
        "title": "Docker",
        "description": "Docker container and image commands",
        "commands": ["docker-build", "docker-push", "docker-up", "docker-down"],
    },
    "compose": {
        "title": "Docker Compose",
        "description": "Docker Compose service commands",
        "commands": ["compose-up", "compose-down", "compose-build"],
    },
    "git": {
        "title": "Git",
        "description": "Git version control commands",
        "commands": ["git-commit", "git-push"],
    },
    "version": {
        "title": "Version",
        "description": "Version management commands",
        "commands": ["version show", "version bump", "version tag"],
    },
}


def detect_project_type(cwd: Path) -> Set[str]:
    """
    Detect project type by analyzing files in the directory.
    
    Returns:
        Set of detected group IDs that might be useful
    """
    detected = set()
    
    # Check for Docker
    if (cwd / "Dockerfile").exists() or (cwd / "docker-compose.yml").exists() or (cwd / "docker-compose.yaml").exists():
        detected.add("docker")
    if (cwd / "docker-compose.yml").exists() or (cwd / "docker-compose.yaml").exists():
        detected.add("compose")
    
    # Check for Python project
    if (cwd / "pyproject.toml").exists() or (cwd / "setup.py").exists() or (cwd / "requirements.txt").exists():
        detected.add("general")
    
    # Check for tests
    if (cwd / "tests").exists() or (cwd / "test").exists() or (cwd / "pytest.ini").exists():
        detected.add("quality")
    
    # Check for Git
    if (cwd / ".git").exists():
        detected.add("git")
        detected.add("version")
    
    # Check for application files
    if (cwd / "src").exists() or (cwd / "app").exists() or (cwd / "main.py").exists():
        detected.add("application")
    
    return detected


def get_project_name(cwd: Path) -> str:
    """Get project name from pyproject.toml or directory name."""
    pyproject_path = cwd / "pyproject.toml"
    if pyproject_path.exists():
        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                if "project" in data and "name" in data["project"]:
                    return data["project"]["name"]
        except Exception:
            pass
    
    return cwd.name or "my-project"


def interactive_init(config_path: Path) -> None:
    """Interactively initialize Sindri config."""
    # Ensure path is resolved to absolute path
    config_path = Path(config_path).resolve()
    
    # If config is in .sindri/, use the parent directory (project root)
    # Otherwise use the config's parent directory
    if config_path.parent.name == ".sindri":
        cwd = config_path.parent.parent
    else:
        cwd = config_path.parent
    
    # Ensure cwd is also resolved
    cwd = cwd.resolve()
    
    console.print("[bold cyan]Sindri Configuration Wizard[/bold cyan]\n")
    
    # Detect project type
    detected_groups = detect_project_type(cwd)
    project_name = get_project_name(cwd)
    
    console.print(f"[dim]Detected project: {project_name}[/dim]")
    if detected_groups:
        console.print(f"[dim]Detected features: {', '.join(sorted(detected_groups))}[/dim]\n")
    
    # Ask for project name
    project_name = Prompt.ask(
        "Project name",
        default=project_name,
    )
    
    # Ask which groups to include
    console.print("\n[bold]Which command groups do you want to include?[/bold]")
    console.print("[dim]Press Enter to accept defaults (detected groups)[/dim]\n")
    
    selected_groups = set()
    
    for group_id, group_info in AVAILABLE_GROUPS.items():
        is_detected = group_id in detected_groups
        default = "Yes" if is_detected else "No"
        
        should_include = Confirm.ask(
            f"  [cyan]{group_info['title']}[/cyan] - {group_info['description']}",
            default=is_detected,
        )
        
        if should_include:
            selected_groups.add(group_id)
    
    # Generate config
    console.print("\n[green]Generating configuration...[/green]")
    
    # Build config dict
    config_dict = {
        "version": "1.0",
        "project_name": project_name,
    }
    
    # Add groups (use simple list format for easier config)
    if selected_groups:
        config_dict["groups"] = sorted(selected_groups)
    
    # Write config
    if config_path.name == "pyproject.toml":
        # Add to pyproject.toml under [tool.sindri]
        from sindri.utils.pyproject_updater import add_sindri_config_to_pyproject
        success, error = add_sindri_config_to_pyproject(config_path, config_dict)
        if not success:
            console.print(f"[red]Error:[/red] {error}")
            raise typer.Exit(1)
        console.print(f"[green]✓[/green] Added [tool.sindri] to [bold]{config_path}[/bold]")
    else:
        # Write standalone sindri.toml file
        config_lines = [
            '# Sindri Configuration',
            '# This file defines commands and workflows for your project',
            '',
            'version = "1.0"',
            f'project_name = "{project_name}"',
            '',
        ]
        
        # Add groups
        if selected_groups:
            group_list = sorted(selected_groups)
            config_lines.append('')
            config_lines.append('# Reference implemented command groups')
            config_lines.append(f'groups = {group_list}')
        
        config_content = '\n'.join(config_lines)
        config_path.write_text(config_content, encoding="utf-8")
        console.print(f"[green]✓[/green] Created config file at [bold]{config_path}[/bold]")
    
    console.print("\nYou can now run [bold]sindri[/bold] to list commands.")

