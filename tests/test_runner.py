"""Tests for the async shell runner."""

import os
from pathlib import Path

import pytest
from sindri.core.shell_runner import run_shell_command, run_shell_commands_parallel
from sindri.core.result import CommandResult


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


class TestCommandResult:
    """Tests for CommandResult."""
    
    def test_command_result_success(self):
        """Test successful command result."""
        result = CommandResult("test", 0, stdout="output", duration=1.5)
        assert result.success
        assert result.exit_code == 0
        assert result.stdout == "output"
        assert result.duration == 1.5
    
    def test_command_result_failure(self):
        """Test failed command result."""
        result = CommandResult("test", 1, stderr="error", error="Command failed")
        assert not result.success
        assert result.exit_code == 1
        assert result.stderr == "error"
        assert result.error == "Command failed"
    
    def test_command_result_repr_success(self):
        """Test CommandResult string representation for success."""
        result = CommandResult("test", 0)
        assert "SUCCESS" in repr(result)
        assert "test" in repr(result)
    
    def test_command_result_repr_failure(self):
        """Test CommandResult string representation for failure."""
        result = CommandResult("test", 1)
        assert "FAILED" in repr(result)
        assert "test" in repr(result)


class TestShellRunner:
    """Tests for run_shell_command."""
    
    @pytest.mark.asyncio
    async def test_run_command_success(self, temp_dir: Path):
        """Test running a successful command."""
        result = await run_shell_command(
            command_id="test",
            shell="echo 'Hello, World!'",
            cwd=temp_dir,
        )
        
        assert result.success
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_command_failure(self, temp_dir: Path):
        """Test running a failing command."""
        result = await run_shell_command(
            command_id="test",
            shell="exit 1",
            cwd=temp_dir,
        )
        
        assert not result.success
        assert result.exit_code == 1
    
    @pytest.mark.asyncio
    async def test_run_command_with_cwd(self, temp_dir: Path):
        """Test running a command with a custom working directory."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        # Create a test file in subdir
        test_file = subdir / "test.txt"
        test_file.write_text("test content")
        
        shell_cmd = "type test.txt" if os.name == "nt" else "cat test.txt"
        result = await run_shell_command(
            command_id="test",
            shell=shell_cmd,
            cwd=subdir,
        )
        
        assert result.success
        assert "test content" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_command_with_env(self, temp_dir: Path):
        """Test running a command with environment variables."""
        if os.name == "nt":
            shell_cmd = "echo %TEST_VAR%"
        else:
            shell_cmd = "echo $TEST_VAR"
        
        result = await run_shell_command(
            command_id="test",
            shell=shell_cmd,
            cwd=temp_dir,
            env={"TEST_VAR": "test_value"},
        )
        
        assert result.success
        assert "test_value" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_command_timeout(self, temp_dir: Path):
        """Test command timeout."""
        if os.name == "nt":
            # Windows doesn't have sleep, use timeout instead
            shell_cmd = "timeout /t 10 /nobreak"
        else:
            shell_cmd = "sleep 10"
        
        result = await run_shell_command(
            command_id="test",
            shell=shell_cmd,
            cwd=temp_dir,
            timeout=1,
        )
        
        assert not result.success
        # Windows timeout returns exit code 1, Unix returns 124
        expected_exit_code = 1 if os.name == "nt" else 124
        assert result.exit_code == expected_exit_code
        # On Windows, timeout command may not set error message, but on Unix it should
        if os.name != "nt":
            assert result.error is not None
            assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_run_command_streaming(self, temp_dir: Path):
        """Test command output streaming."""
        captured_lines = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            captured_lines.append((line, stream_type))
        
        result = await run_shell_command(
            command_id="test",
            shell="echo 'Line 1' && echo 'Line 2'",
            cwd=temp_dir,
            stream_callback=stream_callback,
        )
        
        assert result.success
        assert len(captured_lines) >= 2
        assert any("Line 1" in line[0] for line in captured_lines)
        assert any("Line 2" in line[0] for line in captured_lines)
    
    @pytest.mark.asyncio
    async def test_run_command_stderr_streaming(self, temp_dir: Path):
        """Test stderr streaming."""
        captured_stderr = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            if stream_type == "stderr":
                captured_stderr.append(line)
        
        if os.name == "nt":
            shell_cmd = "echo error >&2"
        else:
            shell_cmd = "echo 'error' >&2"
        
        result = await run_shell_command(
            command_id="test",
            shell=shell_cmd,
            cwd=temp_dir,
            stream_callback=stream_callback,
        )
        
        # Command may succeed (echo to stderr doesn't fail)
        assert len(captured_stderr) > 0 or result.stderr
    
    @pytest.mark.asyncio
    async def test_run_parallel(self, temp_dir: Path):
        """Test running multiple commands in parallel."""
        commands = [
            ("cmd1", "echo 'Command 1'", temp_dir, None),
            ("cmd2", "echo 'Command 2'", temp_dir, None),
            ("cmd3", "echo 'Command 3'", temp_dir, None),
        ]
        
        results = await run_shell_commands_parallel(commands)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].command_id == "cmd1"
        assert results[1].command_id == "cmd2"
        assert results[2].command_id == "cmd3"
    
    @pytest.mark.asyncio
    async def test_run_parallel_with_failure(self, temp_dir: Path):
        """Test running parallel commands with one failure."""
        commands = [
            ("cmd1", "echo 'Command 1'", temp_dir, None),
            ("cmd2", "exit 1", temp_dir, None),
            ("cmd3", "echo 'Command 3'", temp_dir, None),
        ]
        
        results = await run_shell_commands_parallel(commands)
        
        assert len(results) == 3
        assert results[0].success
        assert not results[1].success
        assert results[2].success
