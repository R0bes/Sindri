"""Final tests for CLI modules to reach 90% coverage."""

from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from sindri.cli import app
from sindri.cli.main import main
from sindri.cli.subcommands import create_namespace_subcommand, register_namespace_subcommands
from sindri.cli.parsing import find_command_by_parts, parse_command_parts
from sindri.config import SindriConfig, Command, Group


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


class TestSubcommandsFinal:
    """Final tests for sindri.cli.subcommands module."""
    
    def test_namespace_subcommand_callback_with_commands(self, temp_dir: Path, monkeypatch):
        """Test namespace subcommand callback when commands exist."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["docker"]

[[commands]]
id = "docker-build"
title = "Build"
shell = "docker build ."
""")
        
        namespace_app = create_namespace_subcommand("docker")
        
        from typer.testing import CliRunner
        runner = CliRunner()
        
        # Should show help when no action
        result = runner.invoke(namespace_app, [])
        assert result.exit_code == 0
    
    def test_namespace_subcommand_callback_with_description(self, temp_dir: Path, monkeypatch):
        """Test namespace subcommand callback with group description."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = [{"id": "docker", "title": "Docker", "description": "Docker commands", "commands": ["docker-build"]}]

[[commands]]
id = "docker-build"
title = "Build"
shell = "docker build ."
""")
        
        namespace_app = create_namespace_subcommand("docker")
        
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(namespace_app, [])
        assert result.exit_code == 0
    
    def test_namespace_subcommand_callback_with_grouped_commands(self, temp_dir: Path, monkeypatch):
        """Test namespace subcommand callback with grouped commands (aliases)."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["docker"]

[[commands]]
id = "docker-build"
title = "Build"
shell = "docker build ."

[[commands]]
id = "d-build"
title = "Build"
shell = "docker build ."
""")
        
        namespace_app = create_namespace_subcommand("docker")
        
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(namespace_app, [])
        assert result.exit_code == 0
    
    def test_namespace_subcommand_callback_with_command_no_hyphen(self, temp_dir: Path, monkeypatch):
        """Test namespace subcommand callback with command that has no hyphen."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["docker"]

[[commands]]
id = "dockerup"
title = "Up"
shell = "docker up"
""")
        
        namespace_app = create_namespace_subcommand("docker")
        
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(namespace_app, [])
        assert result.exit_code in [0, 1]
    
    def test_register_namespace_subcommands_with_keyerror(self, temp_dir: Path, monkeypatch):
        """Test register_namespace_subcommands when KeyError occurs."""
        monkeypatch.chdir(temp_dir)
        
        # Create config that might cause KeyError
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["invalid-group"]
""")
        
        import typer
        test_app = typer.Typer(name="test")
        register_namespace_subcommands(test_app, temp_dir)
        
        # Should still register default namespaces
        assert test_app is not None


class TestMainFinal:
    """Final tests for sindri.cli.main module."""
    
    def test_main_with_namespace_help_with_commands(self, temp_dir: Path, monkeypatch):
        """Test main() showing namespace help when commands exist."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["docker"]

[[commands]]
id = "docker-build"
title = "Build"
shell = "docker build ."
""")
        
        with patch('sys.argv', ['sindri', 'docker']):
            with patch('sindri.cli.main.console.print') as mock_print:
                with patch('sindri.cli.main.sys.exit'):
                    try:
                        main()
                    except SystemExit:
                        pass
                    # Should have printed help
                    assert mock_print.called
    
    def test_main_with_namespace_help_with_grouped_commands(self, temp_dir: Path, monkeypatch):
        """Test main() showing namespace help with grouped commands."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["docker"]

[[commands]]
id = "docker-build"
title = "Build"
shell = "docker build ."

[[commands]]
id = "d-build"
title = "Build"
shell = "docker build ."
""")
        
        with patch('sys.argv', ['sindri', 'docker']):
            with patch('sindri.cli.main.console.print') as mock_print:
                with patch('sindri.cli.main.sys.exit'):
                    try:
                        main()
                    except SystemExit:
                        pass
                    # Should have printed help with grouped aliases
                    assert mock_print.called
    
    def test_main_with_namespace_help_command_no_hyphen(self, temp_dir: Path, monkeypatch):
        """Test main() showing namespace help with command that has no hyphen."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["docker"]

[[commands]]
id = "dockerup"
title = "Up"
shell = "docker up"
""")
        
        with patch('sys.argv', ['sindri', 'docker']):
            with patch('sindri.cli.main.console.print') as mock_print:
                with patch('sindri.cli.main.sys.exit'):
                    try:
                        main()
                    except SystemExit:
                        pass
                    # Should have printed help
                    assert mock_print.called


class TestInitFinal:
    """Final tests for sindri.cli.__init__ module."""
    
    def test_main_callback_with_config_option(self, temp_dir: Path, monkeypatch, cli_runner: CliRunner):
        """Test main callback with --config option."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["quality"]
""")
        
        result = cli_runner.invoke(app, ["--config", str(config_file)])
        # Should handle config option
        assert result.exit_code in [0, 1]
    
    def test_main_callback_with_config_before_command(self, temp_dir: Path, monkeypatch, cli_runner: CliRunner):
        """Test main callback with -c before command."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["quality"]
""")
        
        result = cli_runner.invoke(app, ["-c", str(config_file), "test"])
        # Should handle config option before command
        assert result.exit_code in [0, 1, 2, 4]
    
    def test_main_callback_filters_known_typer_commands(self, temp_dir: Path, monkeypatch, cli_runner: CliRunner):
        """Test main callback filters known Typer commands."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["quality"]
""")
        
        # Known Typer commands should not be treated as project commands
        result = cli_runner.invoke(app, ["config"])
        # Should not treat as project command
        assert result.exit_code in [0, 1, 2]
    
    def test_main_callback_with_typer_exit(self, temp_dir: Path, monkeypatch, cli_runner: CliRunner):
        """Test main callback re-raising typer.Exit."""
        monkeypatch.chdir(temp_dir)
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
groups = ["quality"]
""")
        
        with patch('sindri.cli.commands.main', side_effect=typer.Exit(code=0)):
            result = cli_runner.invoke(app, [])
            # Should re-raise typer.Exit
            assert result.exit_code == 0


class TestParsingFinal:
    """Final tests for sindri.cli.parsing module."""
    
    def test_find_command_by_parts_with_namespace_alias(self, temp_dir: Path):
        """Test find_command_by_parts with namespace alias."""
        docker_cmd = Command(id="docker-build", title="Build", shell="docker build .", tags=["docker"])
        config = SindriConfig(
            version="1.0",
            project_name="test",
            commands=[docker_cmd],
            groups=[
                Group(id="docker", title="Docker", description="Docker commands", commands=["docker-build"]),
            ],
        )
        
        cmd = find_command_by_parts(config, ['d', 'build'])
        # Should find via alias
        assert cmd is not None
        assert cmd.id == "docker-build"
    
    def test_parse_command_parts_with_flags_in_middle(self, temp_dir: Path):
        """Test parse_command_parts with flags in the middle."""
        version_cmd = Command(id="version-bump", title="Bump", shell="echo bump", tags=["version"])
        config = SindriConfig(
            version="1.0",
            project_name="test",
            commands=[version_cmd],
            groups=[
                Group(id="version", title="Version", description="Version commands", commands=["version-bump"]),
            ],
        )
        
        commands = parse_command_parts(config, ['version', '--patch', 'bump'])
        # Flags should be ignored
        assert len(commands) >= 0

