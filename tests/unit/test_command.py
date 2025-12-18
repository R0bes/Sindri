"""Tests for sindri.core.command module."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sindri.core.command import (
    CustomCommand,
    ShellCommand,
    is_shell_command,
)
from sindri.core.context import ExecutionContext
from sindri.core.result import CommandResult


class TestShellCommand:
    """Tests for ShellCommand class."""
    
    def test_shell_command_creation(self):
        """Test creating a ShellCommand."""
        cmd = ShellCommand(id="test", shell="echo test")
        assert cmd.id == "test"
        assert cmd.shell == "echo test"
        assert cmd.title == "test"  # Defaults to id
    
    def test_shell_command_with_title(self):
        """Test ShellCommand with explicit title."""
        cmd = ShellCommand(id="test", shell="echo test", title="Test Command")
        assert cmd.title == "Test Command"
    
    def test_shell_command_with_all_fields(self):
        """Test ShellCommand with all optional fields."""
        cmd = ShellCommand(
            id="test",
            shell="echo test",
            title="Test",
            description="A test command",
            group_id="test-group",
            cwd="subdir",
            env={"VAR": "value"},
            env_profile="dev",
            timeout=60,
            retries=3,
            tags=["tag1", "tag2"],
            watch=True,
        )
        assert cmd.description == "A test command"
        assert cmd.group_id == "test-group"
        assert cmd.cwd == "subdir"
        assert cmd.env == {"VAR": "value"}
        assert cmd.env_profile == "dev"
        assert cmd.timeout == 60
        assert cmd.retries == 3
        assert cmd.tags == ["tag1", "tag2"]
        assert cmd.watch is True
    
    def test_shell_command_defaults(self):
        """Test ShellCommand default values."""
        cmd = ShellCommand(id="test", shell="echo test")
        assert cmd.title == "test"
        assert cmd.description is None
        assert cmd.group_id is None
        assert cmd.cwd is None
        assert cmd.env == {}
        assert cmd.env_profile is None
        assert cmd.timeout is None
        assert cmd.retries is None
        assert cmd.tags == []
        assert cmd.watch is False
    
    def test_shell_command_aliases_property(self):
        """Test aliases property."""
        cmd = ShellCommand(id="test", shell="echo test")
        assert cmd.aliases == []
        
        cmd.aliases = ["alias1", "alias2"]
        assert cmd.aliases == ["alias1", "alias2"]
    
    def test_shell_command_all_ids(self):
        """Test all_ids property includes aliases."""
        cmd = ShellCommand(id="test", shell="echo test")
        cmd.aliases = ["alias1", "alias2"]
        
        assert cmd.all_ids == ["test", "alias1", "alias2"]
    
    def test_shell_command_get_shell(self, tmp_path):
        """Test get_shell method."""
        cmd = ShellCommand(id="test", shell="echo test")
        ctx = ExecutionContext(cwd=tmp_path)
        
        assert cmd.get_shell(ctx) == "echo test"
    
    def test_shell_command_validate_success(self, tmp_path):
        """Test validate method with valid cwd."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        cmd = ShellCommand(id="test", shell="echo test", cwd="subdir")
        ctx = ExecutionContext(cwd=tmp_path)
        
        assert cmd.validate(ctx) is None
    
    def test_shell_command_validate_failure(self, tmp_path):
        """Test validate method with invalid cwd."""
        cmd = ShellCommand(id="test", shell="echo test", cwd="nonexistent")
        ctx = ExecutionContext(cwd=tmp_path)
        
        error = cmd.validate(ctx)
        assert error is not None
        assert "does not exist" in error
    
    def test_shell_command_validate_no_cwd(self, tmp_path):
        """Test validate method without cwd."""
        cmd = ShellCommand(id="test", shell="echo test")
        ctx = ExecutionContext(cwd=tmp_path)
        
        assert cmd.validate(ctx) is None
    
    @pytest.mark.asyncio
    async def test_shell_command_execute_success(self, tmp_path):
        """Test execute method with successful command."""
        cmd = ShellCommand(id="test", shell="echo 'Hello World'")
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = await cmd.execute(ctx)
        
        assert result.success
        assert "Hello World" in result.stdout
    
    @pytest.mark.asyncio
    async def test_shell_command_execute_failure(self, tmp_path):
        """Test execute method with failing command."""
        cmd = ShellCommand(id="test", shell="exit 1")
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = await cmd.execute(ctx)
        
        assert not result.success
        assert result.exit_code == 1
    
    @pytest.mark.asyncio
    async def test_shell_command_execute_with_cwd(self, tmp_path):
        """Test execute method with custom cwd."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("test content")
        
        import os
        if os.name == "nt":
            shell_cmd = "type test.txt"
        else:
            shell_cmd = "cat test.txt"
        
        cmd = ShellCommand(id="test", shell=shell_cmd, cwd="subdir")
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = await cmd.execute(ctx)
        
        assert result.success
        assert "test content" in result.stdout
    
    @pytest.mark.asyncio
    async def test_shell_command_execute_with_invalid_cwd(self, tmp_path):
        """Test execute method with invalid cwd."""
        cmd = ShellCommand(id="test", shell="echo test", cwd="nonexistent")
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = await cmd.execute(ctx)
        
        assert not result.success
        assert "does not exist" in result.error
    
    @pytest.mark.asyncio
    async def test_shell_command_execute_dry_run(self, tmp_path):
        """Test execute method in dry run mode."""
        cmd = ShellCommand(id="test", shell="echo test")
        ctx = ExecutionContext(cwd=tmp_path, dry_run=True)
        
        result = await cmd.execute(ctx)
        
        assert result.success
        assert "[DRY RUN]" in result.stdout or "DRY RUN" in result.stdout
    
    @pytest.mark.asyncio
    async def test_shell_command_execute_with_env(self, tmp_path):
        """Test execute method with environment variables."""
        import os
        if os.name == "nt":
            shell_cmd = "echo %TEST_VAR%"
        else:
            shell_cmd = "echo $TEST_VAR"
        
        cmd = ShellCommand(id="test", shell=shell_cmd, env={"TEST_VAR": "test_value"})
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = await cmd.execute(ctx)
        
        assert result.success
        assert "test_value" in result.stdout
    
    @pytest.mark.asyncio
    async def test_shell_command_execute_with_template_expansion(self, tmp_path):
        """Test execute method expands templates."""
        cmd = ShellCommand(id="test", shell="echo 'Project: {project_name}'")
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = await cmd.execute(ctx)
        
        assert result.success
        assert tmp_path.name in result.stdout
    
    @pytest.mark.asyncio
    async def test_shell_command_execute_with_timeout(self, tmp_path):
        """Test execute method with timeout."""
        import os
        if os.name == "nt":
            shell_cmd = "timeout /t 10 /nobreak"
        else:
            shell_cmd = "sleep 10"
        
        cmd = ShellCommand(id="test", shell=shell_cmd, timeout=1)
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = await cmd.execute(ctx)
        
        assert not result.success
        # Windows timeout returns exit code 1, Unix returns 124
        expected_exit_code = 1 if os.name == "nt" else 124
        assert result.exit_code == expected_exit_code
    
    def test_shell_command_from_config_simple(self):
        """Test from_config with simple command."""
        from sindri.config import Command as ConfigCommand
        
        config_cmd = ConfigCommand(id="test", shell="echo test")
        cmd = ShellCommand.from_config(config_cmd)
        
        assert cmd.id == "test"
        assert cmd.shell == "echo test"
    
    def test_shell_command_from_config_with_list_id(self):
        """Test from_config with list id (primary + aliases)."""
        from sindri.config import Command as ConfigCommand
        
        config_cmd = ConfigCommand(id=["test", "alias1", "alias2"], shell="echo test")
        cmd = ShellCommand.from_config(config_cmd)
        
        assert cmd.id == "test"
        assert "alias1" in cmd.aliases
        assert "alias2" in cmd.aliases
    
    def test_shell_command_from_config_with_explicit_aliases(self):
        """Test from_config with explicit aliases."""
        from sindri.config import Command as ConfigCommand
        
        config_cmd = ConfigCommand(id="test", shell="echo test", aliases=["alias1"])
        cmd = ShellCommand.from_config(config_cmd)
        
        assert cmd.id == "test"
        assert "alias1" in cmd.aliases
    
    def test_shell_command_from_config_with_all_fields(self):
        """Test from_config with all fields."""
        from sindri.config import Command as ConfigCommand
        
        config_cmd = ConfigCommand(
            id="test",
            shell="echo test",
            title="Test",
            description="Description",
            cwd="subdir",
            env={"VAR": "value"},
            env_profile="dev",
            timeout=60,
            retries=3,
            tags=["tag1"],
            watch=True,
        )
        cmd = ShellCommand.from_config(config_cmd)
        
        assert cmd.title == "Test"
        assert cmd.description == "Description"
        assert cmd.cwd == "subdir"
        assert cmd.env == {"VAR": "value"}
        assert cmd.env_profile == "dev"
        assert cmd.timeout == 60
        assert cmd.retries == 3
        assert cmd.tags == ["tag1"]
        assert cmd.watch is True


class TestCustomCommand:
    """Tests for CustomCommand base class."""
    
    def test_custom_command_creation(self):
        """Test creating a CustomCommand."""
        class TestCommand(CustomCommand):
            async def execute(self, ctx):
                return CommandResult(command_id=self.id, exit_code=0)
        
        cmd = TestCommand(command_id="test")
        assert cmd.id == "test"
        assert cmd.title == "test"
    
    def test_custom_command_with_title(self):
        """Test CustomCommand with explicit title."""
        class TestCommand(CustomCommand):
            async def execute(self, ctx):
                return CommandResult(command_id=self.id, exit_code=0)
        
        cmd = TestCommand(command_id="test", title="Test Command")
        assert cmd.title == "Test Command"
    
    def test_custom_command_with_description(self):
        """Test CustomCommand with description."""
        class TestCommand(CustomCommand):
            async def execute(self, ctx):
                return CommandResult(command_id=self.id, exit_code=0)
        
        cmd = TestCommand(command_id="test", description="A test command")
        assert cmd.description == "A test command"
    
    def test_custom_command_with_group_id(self):
        """Test CustomCommand with group_id."""
        class TestCommand(CustomCommand):
            async def execute(self, ctx):
                return CommandResult(command_id=self.id, exit_code=0)
        
        cmd = TestCommand(command_id="test", group_id="test-group")
        assert cmd.group_id == "test-group"
        
        cmd.group_id = "new-group"
        assert cmd.group_id == "new-group"
    
    def test_custom_command_get_shell_returns_none(self, tmp_path):
        """Test get_shell returns None for custom commands."""
        class TestCommand(CustomCommand):
            async def execute(self, ctx):
                return CommandResult(command_id=self.id, exit_code=0)
        
        cmd = TestCommand(command_id="test")
        ctx = ExecutionContext(cwd=tmp_path)
        
        assert cmd.get_shell(ctx) is None
    
    def test_custom_command_validate_default(self, tmp_path):
        """Test validate returns None by default."""
        class TestCommand(CustomCommand):
            async def execute(self, ctx):
                return CommandResult(command_id=self.id, exit_code=0)
        
        cmd = TestCommand(command_id="test")
        ctx = ExecutionContext(cwd=tmp_path)
        
        assert cmd.validate(ctx) is None
    
    @pytest.mark.asyncio
    async def test_custom_command_execute(self, tmp_path):
        """Test execute method must be implemented."""
        class TestCommand(CustomCommand):
            async def execute(self, ctx):
                return CommandResult(command_id=self.id, exit_code=0, stdout="Custom output")
        
        cmd = TestCommand(command_id="test")
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = await cmd.execute(ctx)
        
        assert result.success
        assert result.stdout == "Custom output"
    
    def test_custom_command_execute_not_implemented(self, tmp_path):
        """Test that execute must be implemented."""
        class TestCommand(CustomCommand):
            pass
        
        cmd = TestCommand(command_id="test")
        ctx = ExecutionContext(cwd=tmp_path)
        
        with pytest.raises(NotImplementedError):
            # This will fail when execute is called
            import asyncio
            asyncio.run(cmd.execute(ctx))


class TestIsShellCommand:
    """Tests for is_shell_command function."""
    
    def test_is_shell_command_with_shell_command(self, tmp_path):
        """Test is_shell_command returns True for ShellCommand."""
        cmd = ShellCommand(id="test", shell="echo test")
        assert is_shell_command(cmd) is True
    
    def test_is_shell_command_with_custom_command(self, tmp_path):
        """Test is_shell_command returns False for CustomCommand."""
        class TestCommand(CustomCommand):
            async def execute(self, ctx):
                return CommandResult(command_id=self.id, exit_code=0)
        
        cmd = TestCommand(command_id="test")
        assert is_shell_command(cmd) is False
    
    def test_is_shell_command_with_mock_command(self, tmp_path):
        """Test is_shell_command with mock command that returns shell."""
        mock_cmd = MagicMock()
        ctx = ExecutionContext(cwd=tmp_path)
        mock_cmd.get_shell.return_value = "echo test"
        
        assert is_shell_command(mock_cmd) is True
    
    def test_is_shell_command_with_mock_command_no_shell(self, tmp_path):
        """Test is_shell_command with mock command that returns None."""
        mock_cmd = MagicMock()
        ctx = ExecutionContext(cwd=tmp_path)
        mock_cmd.get_shell.return_value = None
        
        assert is_shell_command(mock_cmd) is False
    
    def test_is_shell_command_with_exception(self, tmp_path):
        """Test is_shell_command handles exceptions gracefully."""
        mock_cmd = MagicMock()
        mock_cmd.get_shell.side_effect = Exception("Error")
        
        assert is_shell_command(mock_cmd) is False

