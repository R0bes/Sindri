"""Tests for sindri.core.context module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sindri.core.context import ExecutionContext


class TestExecutionContext:
    """Tests for ExecutionContext dataclass."""
    
    def test_creation_with_path(self, tmp_path):
        """Should accept Path as cwd."""
        ctx = ExecutionContext(cwd=tmp_path)
        assert ctx.cwd == tmp_path
        assert ctx.cwd.is_absolute()
    
    def test_creation_with_string(self, tmp_path):
        """Should convert string cwd to Path."""
        ctx = ExecutionContext(cwd=str(tmp_path))
        assert isinstance(ctx.cwd, Path)
        assert ctx.cwd == tmp_path
    
    def test_default_values(self, tmp_path):
        """Should have sensible defaults."""
        ctx = ExecutionContext(cwd=tmp_path)
        assert ctx.config is None
        assert ctx.env == {}
        assert ctx.dry_run is False
        assert ctx.verbose is False
        assert ctx.stream_callback is None
    
    def test_with_config(self, tmp_path):
        """Should store config."""
        mock_config = MagicMock()
        mock_config.project_name = "test-project"
        
        ctx = ExecutionContext(cwd=tmp_path, config=mock_config)
        assert ctx.config is mock_config
    
    def test_with_env(self, tmp_path):
        """Should store environment variables."""
        ctx = ExecutionContext(
            cwd=tmp_path,
            env={"KEY": "value", "DEBUG": "1"},
        )
        assert ctx.env == {"KEY": "value", "DEBUG": "1"}
    
    def test_dry_run_flag(self, tmp_path):
        """Should store dry_run flag."""
        ctx = ExecutionContext(cwd=tmp_path, dry_run=True)
        assert ctx.dry_run is True
    
    def test_verbose_flag(self, tmp_path):
        """Should store verbose flag."""
        ctx = ExecutionContext(cwd=tmp_path, verbose=True)
        assert ctx.verbose is True


class TestExecutionContextProjectName:
    """Tests for project_name property."""
    
    def test_project_name_from_config(self, tmp_path):
        """Should use config.project_name if set."""
        mock_config = MagicMock()
        mock_config.project_name = "config-project"
        
        ctx = ExecutionContext(cwd=tmp_path, config=mock_config)
        assert ctx.project_name == "config-project"
    
    def test_project_name_fallback_to_dir(self, tmp_path):
        """Should fallback to directory name if no config."""
        ctx = ExecutionContext(cwd=tmp_path)
        assert ctx.project_name == tmp_path.name
    
    def test_project_name_fallback_when_config_none(self, tmp_path):
        """Should fallback if config.project_name is None."""
        mock_config = MagicMock()
        mock_config.project_name = None
        
        ctx = ExecutionContext(cwd=tmp_path, config=mock_config)
        assert ctx.project_name == tmp_path.name


class TestExecutionContextGetEnv:
    """Tests for get_env() method."""
    
    def test_get_env_includes_os_environ(self, tmp_path):
        """Should include os.environ."""
        ctx = ExecutionContext(cwd=tmp_path)
        env = ctx.get_env()
        
        # Should include at least PATH (present on all systems)
        assert "PATH" in env or "Path" in env  # Windows uses "Path"
    
    def test_get_env_includes_context_env(self, tmp_path):
        """Should include context env vars."""
        ctx = ExecutionContext(
            cwd=tmp_path,
            env={"CUSTOM_VAR": "custom_value"},
        )
        env = ctx.get_env()
        assert env["CUSTOM_VAR"] == "custom_value"
    
    def test_get_env_context_overrides_os(self, tmp_path):
        """Context env should override os.environ."""
        with patch.dict(os.environ, {"TEST_VAR": "os_value"}):
            ctx = ExecutionContext(
                cwd=tmp_path,
                env={"TEST_VAR": "context_value"},
            )
            env = ctx.get_env()
            assert env["TEST_VAR"] == "context_value"
    
    def test_get_env_with_profile(self, tmp_path):
        """Should include profile env vars from config."""
        mock_config = MagicMock()
        mock_config.get_env_vars.return_value = {"PROFILE_VAR": "profile_value"}
        
        ctx = ExecutionContext(cwd=tmp_path, config=mock_config)
        env = ctx.get_env(profile="dev")
        
        mock_config.get_env_vars.assert_called_with("dev")
        assert env["PROFILE_VAR"] == "profile_value"
    
    def test_get_env_context_overrides_profile(self, tmp_path):
        """Context env should override profile env."""
        mock_config = MagicMock()
        mock_config.get_env_vars.return_value = {"VAR": "profile_value"}
        
        ctx = ExecutionContext(
            cwd=tmp_path,
            config=mock_config,
            env={"VAR": "context_value"},
        )
        env = ctx.get_env(profile="dev")
        assert env["VAR"] == "context_value"


class TestExecutionContextResolvePath:
    """Tests for resolve_path() method."""
    
    def test_resolve_absolute_path(self, tmp_path):
        """Should return absolute paths unchanged."""
        ctx = ExecutionContext(cwd=tmp_path)
        absolute = Path("/absolute/path")
        
        result = ctx.resolve_path(absolute)
        # On Windows, /absolute/path becomes C:/absolute/path
        # Just check it's still absolute
        assert result.is_absolute()
    
    def test_resolve_relative_path(self, tmp_path):
        """Should resolve relative paths from cwd."""
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = ctx.resolve_path("subdir/file.txt")
        assert result == (tmp_path / "subdir" / "file.txt").resolve()
    
    def test_resolve_string_path(self, tmp_path):
        """Should accept string paths."""
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = ctx.resolve_path("subdir")
        assert isinstance(result, Path)
        assert result == (tmp_path / "subdir").resolve()


class TestExecutionContextChild:
    """Tests for child() method."""
    
    def test_child_inherits_values(self, tmp_path):
        """Child should inherit parent values."""
        ctx = ExecutionContext(
            cwd=tmp_path,
            env={"KEY": "value"},
            dry_run=True,
            verbose=True,
        )
        
        child = ctx.child()
        
        assert child.cwd == ctx.cwd
        assert child.env == ctx.env
        assert child.dry_run == ctx.dry_run
        assert child.verbose == ctx.verbose
    
    def test_child_can_override_cwd(self, tmp_path):
        """Child can override cwd."""
        ctx = ExecutionContext(cwd=tmp_path)
        new_cwd = tmp_path / "subdir"
        new_cwd.mkdir()
        
        child = ctx.child(cwd=new_cwd)
        
        assert child.cwd == new_cwd
        assert ctx.cwd == tmp_path  # Parent unchanged
    
    def test_child_can_override_flags(self, tmp_path):
        """Child can override flags."""
        ctx = ExecutionContext(cwd=tmp_path, dry_run=False)
        
        child = ctx.child(dry_run=True)
        
        assert child.dry_run is True
        assert ctx.dry_run is False  # Parent unchanged
    
    def test_child_merges_env(self, tmp_path):
        """Child env should merge with parent env."""
        ctx = ExecutionContext(
            cwd=tmp_path,
            env={"A": "1", "B": "2"},
        )
        
        child = ctx.child(env={"B": "3", "C": "4"})
        
        assert child.env == {"A": "1", "B": "3", "C": "4"}


class TestExecutionContextTemplateEngine:
    """Tests for template_engine property."""
    
    def test_template_engine_lazy_created(self, tmp_path):
        """Template engine should be created on first access."""
        ctx = ExecutionContext(cwd=tmp_path)
        
        # Access engine
        engine = ctx.template_engine
        
        assert engine is not None
        # Second access should return same instance
        assert ctx.template_engine is engine
    
    def test_expand_templates(self, tmp_path):
        """expand_templates should use engine."""
        ctx = ExecutionContext(cwd=tmp_path)
        
        # project_name should expand to directory name
        result = ctx.expand_templates("Project: {project_name}")
        
        assert tmp_path.name in result
    
    def test_custom_template_engine(self, tmp_path):
        """Should allow setting custom template engine."""
        from sindri.core.templates import TemplateEngine
        
        custom_engine = TemplateEngine()
        custom_engine.register("custom", lambda ctx: "custom_value")
        
        ctx = ExecutionContext(cwd=tmp_path)
        ctx.template_engine = custom_engine
        
        result = ctx.expand_templates("{custom}")
        assert result == "custom_value"
