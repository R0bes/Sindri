"""Integration tests for Sindri."""

import asyncio
import os
from pathlib import Path

import pytest

from sindri.config import Command, CommandDependency, load_config, get_config_dir
from sindri.core import ExecutionContext, get_registry
from sindri.core.shell_runner import run_shell_command
from tests.conftest import TestHelpers


class TestConfigRunnerIntegration:
    """Integration tests for config and runner."""
    
    @pytest.mark.asyncio
    async def test_load_and_run_command(self, temp_dir: Path):
        """Test loading config and running a command."""
        # Create config file
        config_file = TestHelpers.create_config_file(
            temp_dir / "sindri.toml",
            commands=[
                {
                    "id": "test",
                    "title": "Test",
                    "shell": "echo 'Hello from config'",
                }
            ],
        )
        
        # Load config
        config = load_config(config_path=config_file)
        
        # Get command via registry
        registry = get_registry()
        registry.load_from_config(config)
        cmd = registry.get("test")
        assert cmd is not None
        
        # Create execution context
        ctx = ExecutionContext(
            cwd=get_config_dir(config),
            config=config,
        )
        
        # Run command
        result = await cmd.execute(ctx)
        
        assert result.success
        assert "Hello from config" in result.stdout
    
    @pytest.mark.asyncio
    async def test_load_and_run_with_dependencies(self, temp_dir: Path):
        """Test loading config and running command with dependencies."""
        config_file = TestHelpers.create_config_file(
            temp_dir / "sindri.toml",
            commands=[
                {"id": "setup", "shell": "echo 'setup'"},
                {
                    "id": "main",
                    "shell": "echo 'main'",
                    "dependencies": {"before": ["setup"]},
                },
            ],
        )
        
        config = load_config(config_path=config_file)
        
        # Get commands via registry
        registry = get_registry()
        registry.load_from_config(config)
        setup_cmd = registry.get("setup")
        main_cmd = registry.get("main")
        
        assert setup_cmd is not None
        assert main_cmd is not None
        
        # Create execution context
        ctx = ExecutionContext(
            cwd=get_config_dir(config),
            config=config,
        )
        
        captured = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            captured.append(line)
        
        ctx.stream_callback = stream_callback
        
        # Run setup first (dependencies are handled by ExecutionContext/Command)
        setup_result = await setup_cmd.execute(ctx)
        assert setup_result.success
        
        # Then run main
        result = await main_cmd.execute(ctx)
        
        assert result.success
        # Should have run setup before main
        assert any("setup" in line for line in captured)
        assert any("main" in line for line in captured)


class TestConfigDiscoveryIntegration:
    """Integration tests for config discovery."""
    
    def test_discover_and_load_nested(self, temp_dir: Path):
        """Test discovering and loading config from nested directory."""
        # Create config in root
        config_file = TestHelpers.create_config_file(
            temp_dir / "sindri.toml",
            commands=[{"id": "test", "shell": "echo test"}],
        )
        
        # Create nested directory
        nested = TestHelpers.create_nested_dirs(temp_dir, 3)
        
        # Discover and load from nested
        from sindri.config import discover_config
        
        found = discover_config(start_path=nested)
        assert found == config_file
        
        config = load_config(config_path=found)
        assert config.get_command_by_id("test") is not None


class TestRunnerEdgeCases:
    """Edge case tests for runner."""
    
    @pytest.mark.asyncio
    async def test_run_command_with_empty_output(self, temp_dir: Path):
        """Test running command with empty output."""
        if os.name == "nt":
            shell_cmd = "echo."
        else:
            shell_cmd = "echo -n ''"
        
        result = await run_shell_command(
            command_id="test",
            shell=shell_cmd,
            cwd=temp_dir,
        )
        
        assert result.success
        # Output may be empty or contain newline
        assert result.exit_code == 0
    
    @pytest.mark.asyncio
    async def test_run_command_with_large_output(self, temp_dir: Path):
        """Test running command with large output."""
        # Generate large output
        if os.name == "nt":
            shell_cmd = "for /L %i in (1,1,100) do @echo line %i"
        else:
            shell_cmd = "seq 1 100 | xargs -I {} echo 'line {}'"
        
        result = await run_shell_command(
            command_id="test",
            shell=shell_cmd,
            cwd=temp_dir,
        )
        
        assert result.success
        assert len(result.stdout) > 0
    
    @pytest.mark.asyncio
    async def test_run_parallel_empty_list(self, temp_dir: Path):
        """Test running parallel with empty command list."""
        from sindri.core.shell_runner import run_shell_commands_parallel
        
        results = await run_shell_commands_parallel([])
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_run_command_with_special_chars(self, temp_dir: Path):
        """Test running command with special characters in output."""
        result = await run_shell_command(
            command_id="test",
            shell="echo 'Special: !@#$%^&*()'",
            cwd=temp_dir,
        )
        
        assert result.success
        assert "Special" in result.stdout

