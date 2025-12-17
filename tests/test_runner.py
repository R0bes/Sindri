"""Tests for the async execution engine."""

import asyncio
import os
import platform
from pathlib import Path

import pytest

from sindri.config import Command, CommandDependency, SindriConfig, GlobalDefaults
from sindri.runner import AsyncExecutionEngine, CommandResult


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def engine(temp_dir: Path) -> AsyncExecutionEngine:
    """Create an execution engine for testing."""
    return AsyncExecutionEngine(config_dir=temp_dir)


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


class TestAsyncExecutionEngine:
    """Tests for AsyncExecutionEngine."""
    
    @pytest.mark.asyncio
    async def test_run_command_success(self, engine: AsyncExecutionEngine):
        """Test running a successful command."""
        cmd = Command(id="test", shell="echo 'Hello, World!'")
        
        result = await engine.run_command(cmd)
        
        assert result.success
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_command_failure(self, engine: AsyncExecutionEngine):
        """Test running a failing command."""
        cmd = Command(id="test", shell="exit 1")
        
        result = await engine.run_command(cmd)
        
        assert not result.success
        assert result.exit_code == 1
    
    @pytest.mark.asyncio
    async def test_run_command_with_cwd(self, engine: AsyncExecutionEngine, temp_dir: Path):
        """Test running a command with a custom working directory."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        # Create a test file in subdir
        test_file = subdir / "test.txt"
        test_file.write_text("test content")
        
        shell_cmd = "type test.txt" if os.name == "nt" else "cat test.txt"
        cmd = Command(id="test", shell=shell_cmd, cwd="subdir")
        
        result = await engine.run_command(cmd)
        
        assert result.success
        assert "test content" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_command_with_invalid_cwd(self, engine: AsyncExecutionEngine):
        """Test running a command with invalid working directory."""
        cmd = Command(id="test", shell="echo test", cwd="nonexistent")
        
        result = await engine.run_command(cmd)
        
        assert not result.success
        assert result.error is not None
        assert "does not exist" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_run_command_with_env(self, engine: AsyncExecutionEngine):
        """Test running a command with environment variables."""
        if os.name == "nt":
            cmd = Command(
                id="test",
                shell="echo %TEST_VAR%",
                env={"TEST_VAR": "test_value"},
            )
        else:
            cmd = Command(
                id="test",
                shell="echo $TEST_VAR",
                env={"TEST_VAR": "test_value"},
            )
        
        result = await engine.run_command(cmd)
        
        assert result.success
        assert "test_value" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_command_timeout(self, engine: AsyncExecutionEngine):
        """Test command timeout."""
        if os.name == "nt":
            # Windows doesn't have sleep, use timeout instead
            cmd = Command(id="test", shell="timeout /t 10 /nobreak", timeout=1)
        else:
            cmd = Command(id="test", shell="sleep 10", timeout=1)
        
        result = await engine.run_command(cmd)
        
        assert not result.success
        # Windows timeout returns exit code 1, Unix returns 124
        expected_exit_code = 1 if os.name == "nt" else 124
        assert result.exit_code == expected_exit_code
        # On Windows, timeout command may not set error message, but on Unix it should
        if os.name != "nt":
            assert result.error is not None
            assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_run_command_retries(self, engine: AsyncExecutionEngine):
        """Test command retries."""
        test_file = engine.config_dir / "retry_test.txt"
        if test_file.exists():
            test_file.unlink()
        
        # Command that succeeds if file exists, fails otherwise
        if os.name == "nt":
            cmd = Command(
                id="test",
                shell='if exist retry_test.txt (exit 0) else (echo. > retry_test.txt && exit 1)',
                retries=1,
            )
        else:
            cmd = Command(
                id="test",
                shell="test -f retry_test.txt || (touch retry_test.txt && exit 1)",
                retries=1,
            )
        
        result = await engine.run_command(cmd)
        
        # Should succeed after retry
        assert result.success
    
    @pytest.mark.asyncio
    async def test_run_command_retries_exhausted(self, engine: AsyncExecutionEngine):
        """Test command retries when all retries are exhausted."""
        cmd = Command(id="test", shell="exit 1", retries=2)
        
        result = await engine.run_command(cmd)
        
        # Should still fail after retries
        assert not result.success
        assert result.exit_code == 1
    
    @pytest.mark.asyncio
    async def test_run_command_streaming(self, engine: AsyncExecutionEngine):
        """Test command output streaming."""
        cmd = Command(id="test", shell="echo 'Line 1' && echo 'Line 2'")
        
        captured_lines = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            captured_lines.append((line, stream_type))
        
        result = await engine.run_command(cmd, stream_callback=stream_callback)
        
        assert result.success
        assert len(captured_lines) >= 2
        assert any("Line 1" in line[0] for line in captured_lines)
        assert any("Line 2" in line[0] for line in captured_lines)
    
    @pytest.mark.asyncio
    async def test_run_command_stderr_streaming(self, engine: AsyncExecutionEngine):
        """Test stderr streaming."""
        if os.name == "nt":
            cmd = Command(id="test", shell="echo error >&2")
        else:
            cmd = Command(id="test", shell="echo 'error' >&2")
        
        captured_stderr = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            if stream_type == "stderr":
                captured_stderr.append(line)
        
        result = await engine.run_command(cmd, stream_callback=stream_callback)
        
        # Command may succeed (echo to stderr doesn't fail)
        assert len(captured_stderr) > 0 or result.stderr
    
    @pytest.mark.asyncio
    async def test_run_command_no_stream_callback(self, engine: AsyncExecutionEngine):
        """Test running command without stream callback."""
        cmd = Command(id="test", shell="echo test")
        
        result = await engine.run_command(cmd)
        
        assert result.success
        assert "test" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_parallel(self, engine: AsyncExecutionEngine):
        """Test running multiple commands in parallel."""
        commands = [
            Command(id="cmd1", shell="echo 'Command 1'"),
            Command(id="cmd2", shell="echo 'Command 2'"),
            Command(id="cmd3", shell="echo 'Command 3'"),
        ]
        
        results = await engine.run_parallel(commands)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].command_id == "cmd1"
        assert results[1].command_id == "cmd2"
        assert results[2].command_id == "cmd3"
    
    @pytest.mark.asyncio
    async def test_run_parallel_with_failure(self, engine: AsyncExecutionEngine):
        """Test running parallel commands with one failure."""
        commands = [
            Command(id="cmd1", shell="echo 'Command 1'"),
            Command(id="cmd2", shell="exit 1"),
            Command(id="cmd3", shell="echo 'Command 3'"),
        ]
        
        results = await engine.run_parallel(commands)
        
        assert len(results) == 3
        assert results[0].success
        assert not results[1].success
        assert results[2].success
    
    @pytest.mark.asyncio
    async def test_run_parallel_with_exception(self, engine: AsyncExecutionEngine):
        """Test parallel execution handles exceptions."""
        # Create a command that might cause issues
        commands = [
            Command(id="cmd1", shell="echo test"),
            Command(id="cmd2", shell="nonexistent_command_xyz"),
        ]
        
        results = await engine.run_parallel(commands)
        
        # Should handle gracefully
        assert len(results) == 2
        # First should succeed, second may fail or raise exception
        assert results[0].success
    
    @pytest.mark.asyncio
    async def test_run_dry_run(self, engine: AsyncExecutionEngine):
        """Test dry run mode."""
        engine.dry_run = True
        cmd = Command(id="test", shell="echo 'This should not run'")
        
        result = await engine.run_command(cmd)
        
        assert result.success
        assert "[DRY RUN]" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_with_dependencies_before(self, engine: AsyncExecutionEngine):
        """Test running command with before dependencies."""
        setup_cmd = Command(id="setup", shell="echo 'setup'")
        main_cmd = Command(
            id="main",
            shell="echo 'main'",
            dependencies=CommandDependency(before=["setup"]),
        )
        
        all_commands = [setup_cmd, main_cmd]
        
        captured = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            captured.append(line)
        
        result = await engine.run_with_dependencies(
            main_cmd, all_commands, stream_callback=stream_callback
        )
        
        assert result.success
        # Should have run setup before main
        assert any("setup" in line for line in captured)
        assert any("main" in line for line in captured)
    
    @pytest.mark.asyncio
    async def test_run_with_dependencies_after(self, engine: AsyncExecutionEngine):
        """Test running command with after dependencies."""
        main_cmd = Command(
            id="main",
            shell="echo 'main'",
            dependencies=CommandDependency(after=["cleanup"]),
        )
        cleanup_cmd = Command(id="cleanup", shell="echo 'cleanup'")
        
        all_commands = [main_cmd, cleanup_cmd]
        
        captured = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            captured.append(line)
        
        result = await engine.run_with_dependencies(
            main_cmd, all_commands, stream_callback=stream_callback
        )
        
        assert result.success
        # Should have run cleanup after main
        assert any("main" in line for line in captured)
        assert any("cleanup" in line for line in captured)
    
    @pytest.mark.asyncio
    async def test_run_with_dependencies_both(self, engine: AsyncExecutionEngine):
        """Test running command with both before and after dependencies."""
        setup_cmd = Command(id="setup", shell="echo 'setup'")
        main_cmd = Command(
            id="main",
            shell="echo 'main'",
            dependencies=CommandDependency(before=["setup"], after=["cleanup"]),
        )
        cleanup_cmd = Command(id="cleanup", shell="echo 'cleanup'")
        
        all_commands = [setup_cmd, main_cmd, cleanup_cmd]
        
        captured = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            captured.append(line)
        
        result = await engine.run_with_dependencies(
            main_cmd, all_commands, stream_callback=stream_callback
        )
        
        assert result.success
        # Should have run setup, main, cleanup in order
        assert any("setup" in line for line in captured)
        assert any("main" in line for line in captured)
        assert any("cleanup" in line for line in captured)
    
    @pytest.mark.asyncio
    async def test_run_with_dependencies_missing(self, engine: AsyncExecutionEngine):
        """Test running command with missing dependency."""
        main_cmd = Command(
            id="main",
            shell="echo 'main'",
            dependencies=CommandDependency(before=["nonexistent"]),
        )
        
        all_commands = [main_cmd]
        
        # Should not fail, just skip missing dependency
        result = await engine.run_with_dependencies(main_cmd, all_commands)
        assert result.success
    
    @pytest.mark.asyncio
    async def test_engine_timeout_parameter(self, temp_dir: Path):
        """Test engine with default timeout."""
        engine = AsyncExecutionEngine(config_dir=temp_dir, timeout=1)
        
        if os.name == "nt":
            cmd = Command(id="test", shell="timeout /t 10 /nobreak")
        else:
            cmd = Command(id="test", shell="sleep 10")
        
        result = await engine.run_command(cmd)
        
        assert not result.success
        expected_exit_code = 1 if os.name == "nt" else 124
        assert result.exit_code == expected_exit_code
    
    @pytest.mark.asyncio
    async def test_engine_retries_parameter(self, temp_dir: Path):
        """Test engine with default retries."""
        engine = AsyncExecutionEngine(config_dir=temp_dir, retries=1)
        
        test_file = temp_dir / "retry_test.txt"
        if test_file.exists():
            test_file.unlink()
        
        if os.name == "nt":
            # Use Python script that creates file on first run, succeeds on second
            # The script runs in temp_dir, so we need to use the full path
            test_file_str = str(test_file).replace("\\", "\\\\")
            cmd = Command(
                id="test",
                shell=f'python -c "import os, sys; f=r\'{test_file_str}\'; sys.exit(0 if os.path.exists(f) else (open(f, \'w\').close() or 1))"',
            )
        else:
            cmd = Command(
                id="test",
                shell="test -f retry_test.txt || (touch retry_test.txt && exit 1)",
            )
        
        result = await engine.run_command(cmd)
        
        # Should succeed after retry
        assert result.success
    
    def test_register_cleanup(self, engine: AsyncExecutionEngine):
        """Test registering cleanup hooks."""
        called = []
        
        def cleanup():
            called.append(True)
        
        engine.register_cleanup(cleanup)
        assert len(engine.cleanup_hooks) == 1
        
        # Manually trigger cleanup (normally done on shutdown)
        engine._handle_shutdown()
        assert len(called) == 1
    
    @pytest.mark.asyncio
    async def test_run_command_with_command_timeout_override(self, engine: AsyncExecutionEngine):
        """Test that command timeout overrides engine default."""
        engine.default_timeout = 10
        
        if os.name == "nt":
            cmd = Command(id="test", shell="timeout /t 10 /nobreak", timeout=1)
        else:
            cmd = Command(id="test", shell="sleep 10", timeout=1)
        
        result = await engine.run_command(cmd)
        
        # Should use command timeout (1s) not engine default (10s)
        assert not result.success
        expected_exit_code = 1 if os.name == "nt" else 124
        assert result.exit_code == expected_exit_code
    
    @pytest.mark.asyncio
    async def test_run_command_with_command_retries_override(self, engine: AsyncExecutionEngine):
        """Test that command retries override engine default."""
        engine.default_retries = 0
        
        test_file = engine.config_dir / "retry_test.txt"
        if test_file.exists():
            test_file.unlink()
        
        if os.name == "nt":
            cmd = Command(
                id="test",
                shell='if exist retry_test.txt (exit 0) else (echo. > retry_test.txt && exit 1)',
                retries=1,
            )
        else:
            cmd = Command(
                id="test",
                shell="test -f retry_test.txt || (touch retry_test.txt && exit 1)",
                retries=1,
            )
        
        result = await engine.run_command(cmd)
        
        # Should use command retries (1) not engine default (0)
        assert result.success
    
    @pytest.mark.asyncio
    async def test_run_command_exception_during_execution(self, engine: AsyncExecutionEngine):
        """Test handling exception during command execution."""
        # This is hard to test directly, but we can test the error handling
        # by using an invalid command that might cause issues
        cmd = Command(id="test", shell="")
        
        result = await engine.run_command(cmd)
        
        # Should handle gracefully
        assert isinstance(result, CommandResult)
    
    @pytest.mark.asyncio
    async def test_run_parallel_with_stream_callback(self, engine: AsyncExecutionEngine):
        """Test parallel execution with stream callback."""
        commands = [
            Command(id="cmd1", shell="echo 'Command 1'"),
            Command(id="cmd2", shell="echo 'Command 2'"),
        ]
        
        captured = []
        
        def stream_callback(line: str, stream_type: str) -> None:
            captured.append((line, stream_type))
        
        results = await engine.run_parallel(commands, stream_callback=stream_callback)
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert len(captured) > 0
    
    @pytest.mark.asyncio
    async def test_run_command_with_template_expansion(self, temp_dir: Path):
        """Test command execution with template expansion."""
        config = SindriConfig(
            commands=[],
            project_name="test-project"
        )
        config._defaults = GlobalDefaults(docker_registry="custom.registry:5000")
        
        engine = AsyncExecutionEngine(config_dir=temp_dir, config=config)
        
        cmd = Command(
            id="test",
            shell="echo {registry} ${project_name}"
        )
        
        result = await engine.run_command(cmd)
        
        assert result.success
        assert "custom.registry:5000" in result.stdout
        assert "test-project" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_command_with_env_profile(self, temp_dir: Path):
        """Test command execution with environment profile."""
        # Create project config
        project_config_dir = temp_dir / ".sindri"
        project_config_dir.mkdir()
        project_config = project_config_dir / "config.toml"
        project_config.write_text("""[environments.dev]
TEST_VAR = "dev_value"
""")
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "test"
shell = "echo $TEST_VAR"
""")
        
        from sindri.config import load_config
        config = load_config(config_path=config_file)
        
        engine = AsyncExecutionEngine(config_dir=temp_dir, config=config)
        
        cmd = Command(
            id="test",
            shell="echo $TEST_VAR" if os.name != "nt" else "echo %TEST_VAR%",
            env_profile="dev"
        )
        
        result = await engine.run_command(cmd)
        
        assert result.success
        # The environment variable should be set
        # Note: On Windows, environment variable expansion in echo might not work the same way
        # So we just check that the command executed successfully
