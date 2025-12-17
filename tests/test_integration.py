"""Integration tests for Sindri."""

import asyncio
from pathlib import Path

import pytest

from sindri.config import Command, CommandDependency, load_config
from sindri.runner import AsyncExecutionEngine
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
        
        # Get command
        cmd = config.get_command_by_id("test")
        assert cmd is not None
        
        # Run command
        engine = AsyncExecutionEngine(config_dir=temp_dir)
        result = await engine.run_command(cmd)
        
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
        main_cmd = config.get_command_by_id("main")
        
        engine = AsyncExecutionEngine(config_dir=temp_dir)
        
        captured = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            captured.append(line)
        
        result = await engine.run_with_dependencies(
            main_cmd, config.commands, stream_callback=stream_callback
        )
        
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
        engine = AsyncExecutionEngine(config_dir=temp_dir)
        cmd = Command(id="test", shell="echo -n ''")
        
        result = await engine.run_command(cmd)
        
        assert result.success
        # Output may be empty or contain newline
        assert result.exit_code == 0
    
    @pytest.mark.asyncio
    async def test_run_command_with_large_output(self, temp_dir: Path):
        """Test running command with large output."""
        engine = AsyncExecutionEngine(config_dir=temp_dir)
        # Generate large output
        if os.name == "nt":
            cmd = Command(id="test", shell="for /L %i in (1,1,100) do @echo line %i")
        else:
            cmd = Command(id="test", shell="seq 1 100 | xargs -I {} echo 'line {}'")
        
        result = await engine.run_command(cmd)
        
        assert result.success
        assert len(result.stdout) > 0
    
    @pytest.mark.asyncio
    async def test_run_parallel_empty_list(self, temp_dir: Path):
        """Test running parallel with empty command list."""
        engine = AsyncExecutionEngine(config_dir=temp_dir)
        
        results = await engine.run_parallel([])
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_run_command_with_special_chars(self, temp_dir: Path):
        """Test running command with special characters in output."""
        engine = AsyncExecutionEngine(config_dir=temp_dir)
        cmd = Command(id="test", shell="echo 'Special: !@#$%^&*()'")
        
        result = await engine.run_command(cmd)
        
        assert result.success
        assert "Special" in result.stdout


# Import os for platform checks
import os

