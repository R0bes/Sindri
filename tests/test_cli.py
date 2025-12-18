"""Tests for CLI interface."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sindri.cli import app
from sindri.cli.template import get_default_config_template
from sindri.cli.parsing import (
    format_command_id_for_display,
    resolve_command_id,
    find_command_by_parts,
)
from sindri.config import load_config, SindriConfig, Command


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


class TestConfigTemplate:
    """Tests for config template generation."""
    
    def test_get_default_config_template(self):
        """Test getting default config template."""
        template = get_default_config_template()
        
        assert "version" in template
        assert "[[commands]]" in template
        assert "[[groups]]" in template
        assert "setup" in template
        assert "docker" in template


class TestInitCommand:
    """Tests for init command."""
    
    def test_init_creates_config_file(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test that init creates a config file."""
        monkeypatch.chdir(temp_dir)
        
        result = cli_runner.invoke(app, ["init", "--no-interactive"])
        
        assert result.exit_code == 0
        config_file = temp_dir / ".sindri" / "sindri.toml"
        assert config_file.exists()
        assert "version" in config_file.read_text()
    
    def test_init_with_custom_path(self, cli_runner: CliRunner, temp_dir: Path):
        """Test init with custom config path."""
        config_path = temp_dir / "custom.toml"
        
        result = cli_runner.invoke(app, ["init", "--config", str(config_path), "--no-interactive"])
        
        assert result.exit_code == 0
        assert config_path.exists()
    
    def test_init_overwrites_existing(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test init with existing config file."""
        monkeypatch.chdir(temp_dir)
        sindri_dir = temp_dir / ".sindri"
        sindri_dir.mkdir(exist_ok=True)
        config_file = sindri_dir / "sindri.toml"
        config_file.write_text("old content")
        
        # Mock typer.confirm to return True
        with patch("typer.confirm", return_value=True):
            result = cli_runner.invoke(app, ["init", "--no-interactive"])
        
        assert result.exit_code == 0
        assert config_file.exists()
        # Content should be updated
        content = config_file.read_text()
        assert "old content" not in content
        assert "version" in content
    
    def test_init_does_not_overwrite_if_cancelled(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test init cancels overwrite if user says no."""
        monkeypatch.chdir(temp_dir)
        sindri_dir = temp_dir / ".sindri"
        sindri_dir.mkdir(exist_ok=True)
        config_file = sindri_dir / "sindri.toml"
        original_content = "old content"
        config_file.write_text(original_content)
        
        # Mock typer.confirm to return False
        with patch("typer.confirm", return_value=False):
            result = cli_runner.invoke(app, ["init", "--no-interactive"])
        
        assert result.exit_code == 0
        # Content should be unchanged
        assert config_file.read_text() == original_content


class TestRunCommand:
    """Tests for run command."""
    
    def test_run_command_success(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running a command successfully."""
        monkeypatch.chdir(temp_dir)
        
        # Create config file
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Hello"
shell = "echo 'Hello'"
""")
        
        result = cli_runner.invoke(app, ["run", "hello"])
        
        assert result.exit_code == 0
        assert "Hello" in result.stdout or "SUCCESS" in result.stdout
    
    def test_run_command_not_found(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running a non-existent command."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text('version = "1.0"\n[[commands]]\nid = "hello"\nshell = "echo hello"')
        
        result = cli_runner.invoke(app, ["run", "nonexistent"])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "Unknown command" in result.stdout
    
    def test_run_command_no_config(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running command without config file."""
        monkeypatch.chdir(temp_dir)
        
        result = cli_runner.invoke(app, ["run", "hello"])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "No Sindri config" in result.stdout
    
    def test_run_command_with_config_path(self, cli_runner: CliRunner, temp_dir: Path):
        """Test running command with custom config path."""
        config_file = temp_dir / "custom.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Hello"
shell = "echo 'Hello'"
""")
        
        result = cli_runner.invoke(app, ["run", "hello", "--config", str(config_file)])
        
        assert result.exit_code == 0
    
    def test_run_command_dry_run(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running command in dry-run mode."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Hello"
shell = "echo 'Hello'"
""")
        
        result = cli_runner.invoke(app, ["run", "hello", "--dry-run"])
        
        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout.upper()
    
    def test_run_command_parallel(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running multiple commands in parallel."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "cmd1"
title = "Command 1"
shell = "echo 'Command 1'"

[[commands]]
id = "cmd2"
title = "Command 2"
shell = "echo 'Command 2'"
""")
        
        result = cli_runner.invoke(app, ["run", "cmd1", "cmd2", "--parallel"])
        
        assert result.exit_code == 0
    
    def test_run_command_with_timeout(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running command with timeout."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Test"
shell = "echo 'Hello'"
""")
        
        result = cli_runner.invoke(app, ["run", "hello", "--timeout", "10"])
        
        assert result.exit_code == 0
    
    def test_run_command_with_retries(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running command with retries."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Test"
shell = "echo 'Hello'"
""")
        
        result = cli_runner.invoke(app, ["run", "hello", "--retries", "2"])
        
        assert result.exit_code == 0


class TestListCommand:
    """Tests for list command."""
    
    def test_list_commands(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test listing commands."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "cmd1"
title = "Command 1"
shell = "echo 1"

[[commands]]
id = "cmd2"
title = "Command 2"
shell = "echo 2"
""")
        
        result = cli_runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "cmd1" in result.stdout
        assert "cmd2" in result.stdout
    
    def test_list_no_config(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test listing commands without config."""
        monkeypatch.chdir(temp_dir)
        
        result = cli_runner.invoke(app, ["list"])
        
        assert result.exit_code == 1




class TestConfigInitCommand:
    """Tests for config init command."""
    
    def test_config_init_creates_config_file(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test that config init creates a config file."""
        monkeypatch.chdir(temp_dir)
        
        result = cli_runner.invoke(app, ["config", "init", "--no-interactive"])
        
        assert result.exit_code == 0
        config_file = temp_dir / ".sindri" / "sindri.toml"
        assert config_file.exists()
        assert "version" in config_file.read_text()
    
    def test_config_init_with_custom_path(self, cli_runner: CliRunner, temp_dir: Path):
        """Test config init with custom config path."""
        config_path = temp_dir / "custom.toml"
        
        result = cli_runner.invoke(app, ["config", "init", "--config", str(config_path), "--no-interactive"])
        
        assert result.exit_code == 0
        assert config_path.exists()
    
    def test_config_init_overwrites_existing(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test config init with existing config file."""
        monkeypatch.chdir(temp_dir)
        sindri_dir = temp_dir / ".sindri"
        sindri_dir.mkdir(exist_ok=True)
        config_file = sindri_dir / "sindri.toml"
        config_file.write_text("old content")
        
        # Mock typer.confirm to return True
        with patch("typer.confirm", return_value=True):
            result = cli_runner.invoke(app, ["config", "init", "--no-interactive"])
        
        assert result.exit_code == 0
        assert config_file.exists()
        # Content should be updated
        content = config_file.read_text()
        assert "old content" not in content
        assert "version" in content
    
    def test_config_init_does_not_overwrite_if_cancelled(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test config init cancels overwrite if user says no."""
        monkeypatch.chdir(temp_dir)
        sindri_dir = temp_dir / ".sindri"
        sindri_dir.mkdir(exist_ok=True)
        config_file = sindri_dir / "sindri.toml"
        original_content = "old content"
        config_file.write_text(original_content)
        
        # Mock typer.confirm to return False
        with patch("typer.confirm", return_value=False):
            result = cli_runner.invoke(app, ["config", "init", "--no-interactive"])
        
        assert result.exit_code == 0
        # Content should be unchanged
        assert config_file.read_text() == original_content


class TestConfigValidateCommand:
    """Tests for config validate command."""
    
    def test_config_validate_success(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test validating a valid config file."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Test"
shell = "echo 'Hello'"
""")
        
        result = cli_runner.invoke(app, ["config", "validate"])
        
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower() or "[OK]" in result.stdout
    
    def test_config_validate_with_verbose(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test validating with verbose output."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
project_name = "test-project"
[[commands]]
id = "hello"
title = "Test"
shell = "echo 'Hello'"
""")
        
        result = cli_runner.invoke(app, ["config", "validate", "--verbose"])
        
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower() or "[OK]" in result.stdout
        assert "Config file" in result.stdout or "Workspace" in result.stdout
    
    def test_config_validate_no_config(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test validating without config file."""
        monkeypatch.chdir(temp_dir)
        
        result = cli_runner.invoke(app, ["config", "validate"])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "No Sindri config" in result.stdout
    
    def test_config_validate_invalid_config(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test validating an invalid config file."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("invalid toml content !!!")
        
        result = cli_runner.invoke(app, ["config", "validate"])
        
        assert result.exit_code == 1
        assert "failed" in result.stdout.lower() or "[FAIL]" in result.stdout
    
    def test_config_validate_with_custom_path(self, cli_runner: CliRunner, temp_dir: Path):
        """Test validating with custom config path."""
        config_file = temp_dir / "custom.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Test"
shell = "echo 'Hello'"
""")
        
        result = cli_runner.invoke(app, ["config", "validate", "--config", str(config_file)])
        
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower() or "[OK]" in result.stdout
    
    def test_config_validate_with_groups(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test validating config with groups."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "cmd1"
title = "Command 1"
shell = "echo 1"

[[commands]]
id = "cmd2"
title = "Command 2"
shell = "echo 2"

[[groups]]
id = "group1"
title = "Group 1"
order = 1
commands = ["cmd1", "cmd2"]
""")
        
        result = cli_runner.invoke(app, ["config", "validate", "--verbose"])
        
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower() or "[OK]" in result.stdout
        assert "Groups" in result.stdout or "groups" in result.stdout.lower()


class TestHelperFunctions:
    """Tests for CLI helper functions."""
    
    def test_format_command_id_for_display_docker(self):
        """Test formatting docker command IDs."""
        assert format_command_id_for_display("docker-restart") == "docker restart"
        assert format_command_id_for_display("docker-up") == "docker up"
        assert format_command_id_for_display("docker-down") == "docker down"
    
    def test_format_command_id_for_display_compose(self):
        """Test formatting compose command IDs."""
        assert format_command_id_for_display("compose-up") == "compose up"
        assert format_command_id_for_display("compose-down") == "compose down"
    
    def test_format_command_id_for_display_git(self):
        """Test formatting git command IDs."""
        assert format_command_id_for_display("git-commit") == "git commit"
        assert format_command_id_for_display("git-push") == "git push"
    
    def test_format_command_id_for_display_simple(self):
        """Test formatting simple command IDs."""
        assert format_command_id_for_display("setup-venv") == "setup venv"
        assert format_command_id_for_display("setup-install") == "setup install"
    
    def test_resolve_command_id_single_part(self):
        """Test resolving single part command ID."""
        assert resolve_command_id(["docker-up"]) == "docker-up"
        assert resolve_command_id(["setup-venv"]) == "setup-venv"
    
    def test_resolve_command_id_two_parts(self):
        """Test resolving two-part command ID."""
        assert resolve_command_id(["docker", "up"]) == "docker-up"
        assert resolve_command_id(["compose", "down"]) == "compose-down"
        assert resolve_command_id(["git", "commit"]) == "git-commit"
    
    def test_resolve_command_id_with_alias(self):
        """Test resolving command ID with alias."""
        assert resolve_command_id(["d", "up"]) == "docker-up"
        assert resolve_command_id(["c", "up"]) == "compose-up"
        assert resolve_command_id(["g", "commit"]) == "git-commit"
    
    def test_resolve_command_id_empty(self):
        """Test resolving empty command parts."""
        assert resolve_command_id([]) is None
    
    def test_find_command_by_parts(self, temp_dir: Path):
        """Test finding command by parts."""
        config = SindriConfig(
            commands=[
                Command(id="docker-up", shell="docker up"),
                Command(id="compose-up", shell="compose up"),
                Command(id="setup-venv", shell="echo setup venv"),
            ]
        )
        
        # Test direct match
        cmd = find_command_by_parts(config, ["docker", "up"])
        assert cmd is not None
        assert cmd.id == "docker-up"
        
        # Test with alias
        cmd = find_command_by_parts(config, ["d", "up"])
        assert cmd is not None
        assert cmd.id == "docker-up"
        
        # Test single command
        cmd = find_command_by_parts(config, ["setup-venv"])
        assert cmd is not None
        assert cmd.id == "setup-venv"
        
        # Test namespace command
        cmd = find_command_by_parts(config, ["setup", "venv"])
        assert cmd is not None
        assert cmd.id == "setup-venv"
        
        # Test non-existent
        cmd = find_command_by_parts(config, ["nonexistent"])
        assert cmd is None


class TestListCommandWithGroups:
    """Tests for list command with groups."""
    
    def test_list_with_groups(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test listing commands with groups."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "cmd1"
title = "Command 1"
shell = "echo 1"

[[commands]]
id = "cmd2"
title = "Command 2"
shell = "echo 2"

[[groups]]
id = "group1"
title = "Group 1"
order = 1
commands = ["cmd1", "cmd2"]
""")
        
        result = cli_runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "cmd1" in result.stdout or "Command 1" in result.stdout
        assert "cmd2" in result.stdout or "Command 2" in result.stdout
        assert "Group 1" in result.stdout or "group1" in result.stdout.lower() or "Available Commands" in result.stdout
    
    def test_list_with_long_description(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test listing commands with long descriptions that get truncated."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        long_desc = "A" * 100  # Very long description
        config_file.write_text(f"""version = "1.0"
[[commands]]
id = "cmd1"
title = "Command 1"
description = "{long_desc}"
shell = "echo 1"
""")
        
        result = cli_runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "cmd1" in result.stdout
    
    def test_list_with_empty_groups(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test listing when group has no commands."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "cmd1"
title = "Command 1"
shell = "echo 1"

[[groups]]
id = "group1"
title = "Group 1"
order = 1
commands = ["cmd1"]

[[groups]]
id = "group2"
title = "Group 2"
order = 2
commands = []
""")
        
        result = cli_runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "cmd1" in result.stdout


class TestMainCommand:
    """Tests for main command (default: list commands)."""
    
    def test_main_default_cli_mode(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test main command defaults to CLI mode (list commands)."""
        # Create config in .sindri/sindri.toml (new default location)
        sindri_dir = temp_dir / ".sindri"
        sindri_dir.mkdir(exist_ok=True)
        config_file = sindri_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Test"
shell = "echo test"
""")
        
        # Use absolute path to ensure it works with CliRunner
        # CliRunner doesn't respect monkeypatch.chdir, so we use absolute paths
        config_path = config_file.resolve()
        result = cli_runner.invoke(app, ["--config", str(config_path)])
        
        # Debug output if test fails
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.stdout}")
            print(f"Exception: {result.exception}")
        
        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}. Output: {result.stdout}"
        assert "test" in result.stdout or "Test" in result.stdout
    
    def test_main_default_with_groups(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test main command in CLI mode with groups."""
        # Create config in .sindri/sindri.toml (new default location)
        sindri_dir = temp_dir / ".sindri"
        sindri_dir.mkdir(exist_ok=True)
        config_file = sindri_dir / "sindri.toml"
        config_content = """version = "1.0"
[[commands]]
id = "cmd1"
title = "Command 1"
shell = "echo 1"

[[commands]]
id = "cmd2"
title = "Command 2"
shell = "echo 2"

[[groups]]
id = "group1"
title = "Group 1"
order = 1
commands = ["cmd1", "cmd2"]
"""
        config_file.write_text(config_content)
        
        # Use absolute path to ensure it works with CliRunner
        # CliRunner doesn't respect monkeypatch.chdir, so we use absolute paths
        config_path = config_file.resolve()
        result = cli_runner.invoke(app, ["--config", str(config_path)])
        
        assert result.exit_code == 0
        assert "cmd1" in result.stdout
        assert "cmd2" in result.stdout
    
    def test_main_default_no_config(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test main command in CLI mode without config."""
        monkeypatch.chdir(temp_dir)
        
        result = cli_runner.invoke(app, [])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "No Sindri config" in result.stdout


class TestRunCommandMultiPart:
    """Tests for run command with multi-part commands."""
    
    def test_run_docker_up(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running docker up command."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "docker-up"
title = "Up"
shell = "echo 'docker up'"
""")
        
        result = cli_runner.invoke(app, ["run", "docker", "up"])
        
        assert result.exit_code == 0
    
    def test_run_docker_up_with_alias(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running docker up with alias."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "docker-up"
title = "Up"
shell = "echo 'docker up'"
""")
        
        result = cli_runner.invoke(app, ["run", "d", "up"])
        
        assert result.exit_code == 0
    
    def test_run_git_commit(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running git commit command."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "git-commit"
title = "Commit"
shell = "echo 'git commit'"
""")
        
        result = cli_runner.invoke(app, ["run", "git", "commit"])
        
        assert result.exit_code == 0
    
    def test_run_multiple_commands(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running multiple commands."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "docker-up"
title = "Up"
shell = "echo 'docker up'"

[[commands]]
id = "docker-down"
title = "Down"
shell = "echo 'docker down'"
""")
        
        result = cli_runner.invoke(app, ["run", "docker", "up", "docker", "down"])
        
        assert result.exit_code == 0
    
    def test_run_command_failure(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running a command that fails."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "hello"
title = "Test"
shell = "exit 1"
""")
        
        result = cli_runner.invoke(app, ["run", "hello"])
        
        assert result.exit_code == 1
        assert "FAIL" in result.stdout or "failed" in result.stdout.lower()
    
    def test_run_command_failure_with_error(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test running a command that fails with error message."""
        import os
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        if os.name == "nt":
            shell_cmd = "echo error >&2 && exit 1"
        else:
            shell_cmd = "echo 'error' >&2 && exit 1"
        
        config_file.write_text(f"""version = "1.0"
[[commands]]
id = "hello"
title = "Test"
shell = "{shell_cmd}"
""")
        
        result = cli_runner.invoke(app, ["run", "hello"])
        
        assert result.exit_code == 1
    
    def test_run_command_stop_on_failure(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        """Test that sequential execution stops on first failure."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "cmd1"
title = "Command 1"
shell = "exit 1"

[[commands]]
id = "cmd2"
title = "Command 2"
shell = "echo 'Command 2'"
""")
        
        result = cli_runner.invoke(app, ["run", "cmd1", "cmd2"])
        
        # Should fail and not run cmd2
        assert result.exit_code == 1

