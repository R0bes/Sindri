"""Tests for sindri.core.result module."""

import pytest
from sindri.core.result import CommandResult


class TestCommandResult:
    """Tests for CommandResult dataclass."""
    
    def test_success_on_zero_exit_code(self):
        """Exit code 0 should set success=True."""
        result = CommandResult(command_id="test", exit_code=0)
        assert result.success is True
        assert result.exit_code == 0
    
    def test_failure_on_nonzero_exit_code(self):
        """Non-zero exit code should set success=False."""
        result = CommandResult(command_id="test", exit_code=1)
        assert result.success is False
        
        result = CommandResult(command_id="test", exit_code=127)
        assert result.success is False
    
    def test_default_values(self):
        """Default values should be empty strings and zero duration."""
        result = CommandResult(command_id="test", exit_code=0)
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.duration == 0.0
        assert result.error is None
    
    def test_with_output(self):
        """Should store stdout and stderr."""
        result = CommandResult(
            command_id="build",
            exit_code=0,
            stdout="Build complete",
            stderr="Warning: deprecated API",
            duration=1.5,
        )
        assert result.stdout == "Build complete"
        assert result.stderr == "Warning: deprecated API"
        assert result.duration == 1.5
    
    def test_with_error(self):
        """Should store error message."""
        result = CommandResult(
            command_id="deploy",
            exit_code=1,
            error="Connection refused",
        )
        assert result.error == "Connection refused"
        assert result.success is False
    
    def test_repr_success(self):
        """Repr should show SUCCESS for exit_code=0."""
        result = CommandResult(command_id="test", exit_code=0)
        assert "SUCCESS" in repr(result)
        assert "test" in repr(result)
    
    def test_repr_failure(self):
        """Repr should show FAILED for non-zero exit_code."""
        result = CommandResult(command_id="test", exit_code=1)
        assert "FAILED" in repr(result)
    
    def test_bool_true_on_success(self):
        """Boolean conversion should return True on success."""
        result = CommandResult(command_id="test", exit_code=0)
        assert bool(result) is True
        
        # Should work in if statements
        if result:
            passed = True
        else:
            passed = False
        assert passed is True
    
    def test_bool_false_on_failure(self):
        """Boolean conversion should return False on failure."""
        result = CommandResult(command_id="test", exit_code=1)
        assert bool(result) is False
    
    def test_output_property_combined(self):
        """Output property should combine stdout and stderr."""
        result = CommandResult(
            command_id="test",
            exit_code=0,
            stdout="Line 1",
            stderr="Line 2",
        )
        assert "Line 1" in result.output
        assert "Line 2" in result.output
    
    def test_output_property_stdout_only(self):
        """Output property should work with stdout only."""
        result = CommandResult(
            command_id="test",
            exit_code=0,
            stdout="Output",
        )
        assert result.output == "Output"
    
    def test_output_property_empty(self):
        """Output property should return empty string when no output."""
        result = CommandResult(command_id="test", exit_code=0)
        assert result.output == ""
    
    def test_raise_on_error_success(self):
        """raise_on_error should not raise on success."""
        result = CommandResult(command_id="test", exit_code=0)
        # Should not raise
        result.raise_on_error()
        result.raise_on_error("Custom message")
    
    def test_raise_on_error_failure(self):
        """raise_on_error should raise RuntimeError on failure."""
        result = CommandResult(
            command_id="test",
            exit_code=1,
            error="Something went wrong",
        )
        with pytest.raises(RuntimeError) as exc_info:
            result.raise_on_error()
        assert "Something went wrong" in str(exc_info.value)
    
    def test_raise_on_error_with_message(self):
        """raise_on_error should include custom message prefix."""
        result = CommandResult(
            command_id="test",
            exit_code=1,
            error="Failed",
        )
        with pytest.raises(RuntimeError) as exc_info:
            result.raise_on_error("Build step")
        assert "Build step" in str(exc_info.value)
        assert "Failed" in str(exc_info.value)
    
    def test_raise_on_error_uses_stderr_if_no_error(self):
        """raise_on_error should use stderr if error is None."""
        result = CommandResult(
            command_id="test",
            exit_code=1,
            stderr="Error from stderr",
        )
        with pytest.raises(RuntimeError) as exc_info:
            result.raise_on_error()
        assert "Error from stderr" in str(exc_info.value)
    
    def test_raise_on_error_uses_exit_code_if_no_message(self):
        """raise_on_error should mention exit code if no error or stderr."""
        result = CommandResult(
            command_id="test",
            exit_code=127,
        )
        with pytest.raises(RuntimeError) as exc_info:
            result.raise_on_error()
        assert "127" in str(exc_info.value)
