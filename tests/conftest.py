"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from sindri.config import Command, CommandDependency, Group, SindriConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_command() -> Command:
    """Create a sample command for testing."""
    return Command(
        id="test-command",
        title="Test Command",
        description="A test command",
        shell="echo 'Hello, World!'",
        tags=["test"],
    )


@pytest.fixture
def sample_commands() -> List[Command]:
    """Create multiple sample commands."""
    return [
        Command(id="cmd1", title="Command 1", shell="echo 1", tags=["test"]),
        Command(id="cmd2", title="Command 2", shell="echo 2", tags=["test"]),
        Command(id="cmd3", title="Command 3", shell="echo 3", tags=["other"]),
    ]


@pytest.fixture
def sample_config(sample_commands: List[Command]) -> SindriConfig:
    """Create a sample SindriConfig for testing."""
    return SindriConfig(
        version="1.0",
        project_name="test-project",
        commands=sample_commands,
        groups=[
            Group(
                id="test-group",
                title="Test Group",
                description="A test group",
                order=1,
                commands=["cmd1", "cmd2"],
            )
        ],
    )


@pytest.fixture
def sample_config_file(temp_dir: Path) -> Path:
    """Create a sample config file for testing."""
    config_content = """version = "1.0"
project_name = "test-project"

[[commands]]
id = "test-command"
title = "Test Command"
description = "A test command"
shell = "echo 'Hello, World!'"
tags = ["test"]

[[commands]]
id = "test-command-2"
title = "Test Command 2"
description = "Another test command"
shell = "echo 'Goodbye, World!'"
tags = ["test"]

[[groups]]
id = "test-group"
title = "Test Group"
description = "A test group"
order = 1
commands = ["test-command", "test-command-2"]
"""
    config_file = temp_dir / "sindri.toml"
    config_file.write_text(config_content, encoding="utf-8")
    return config_file


@pytest.fixture
def config_with_dependencies() -> SindriConfig:
    """Create a config with command dependencies."""
    return SindriConfig(
        commands=[
            Command(id="setup", shell="echo setup"),
            Command(
                id="main",
                shell="echo main",
                dependencies=CommandDependency(before=["setup"], after=["cleanup"]),
            ),
            Command(id="cleanup", shell="echo cleanup"),
        ]
    )


@pytest.fixture
def config_with_compose_profiles() -> SindriConfig:
    """Create a config with compose profiles."""
    from sindri.config import ComposeProfile
    
    return SindriConfig(
        commands=[Command(id="test", shell="echo test")],
        compose_profiles=[
            ComposeProfile(
                id="dev",
                title="Development",
                profiles=["dev"],
                command="up",
                flags=["-d"],
            )
        ],
    )


@pytest.fixture
def mock_project_structure(temp_dir: Path) -> Path:
    """Create a mock project structure with markers."""
    # Create .git marker
    (temp_dir / ".git").mkdir()
    # Create pyproject.toml
    (temp_dir / "pyproject.toml").write_text("[project]\nname = 'test'")
    return temp_dir


class TestHelpers:
    """Helper functions for tests."""
    
    @staticmethod
    def create_config_file(
        path: Path,
        commands: Optional[List[Dict]] = None,
        groups: Optional[List[Dict]] = None,
        version: str = "1.0",
    ) -> Path:
        """Create a config file with specified content."""
        content = f'version = "{version}"\n\n'
        
        if commands:
            for cmd in commands:
                content += "[[commands]]\n"
                for key, value in cmd.items():
                    if isinstance(value, list):
                        value_str = "[" + ", ".join(f'"{v}"' for v in value) + "]"
                    elif isinstance(value, bool):
                        value_str = str(value).lower()
                    elif isinstance(value, dict):
                        # Handle dependencies
                        deps_str = "{ "
                        deps_parts = []
                        if "before" in value:
                            deps_parts.append(f'before = {value["before"]}')
                        if "after" in value:
                            deps_parts.append(f'after = {value["after"]}')
                        deps_str += ", ".join(deps_parts) + " }"
                        value_str = deps_str
                    else:
                        value_str = f'"{value}"'
                    content += f"{key} = {value_str}\n"
                content += "\n"
        
        if groups:
            for group in groups:
                content += "[[groups]]\n"
                for key, value in group.items():
                    if isinstance(value, list):
                        value_str = "[" + ", ".join(f'"{v}"' for v in value) + "]"
                    else:
                        value_str = f'"{value}"'
                    content += f"{key} = {value_str}\n"
                content += "\n"
        
        path.write_text(content, encoding="utf-8")
        return path
    
    @staticmethod
    def create_nested_dirs(base: Path, depth: int) -> Path:
        """Create nested directories."""
        current = base
        for i in range(depth):
            current = current / f"level{i}"
            current.mkdir()
        return current
