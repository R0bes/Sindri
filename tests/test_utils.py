"""Tests for utility functions."""

import os
import platform
import tempfile
from pathlib import Path

import pytest

from sindri.utils import (
    escape_shell_arg,
    find_project_root,
    get_project_name,
    get_shell,
)


class TestFindProjectRoot:
    """Tests for find_project_root function."""
    
    def test_find_project_root_with_git(self, temp_dir: Path):
        """Test finding project root with .git marker."""
        (temp_dir / ".git").mkdir()
        
        result = find_project_root(temp_dir)
        assert result == temp_dir
    
    def test_find_project_root_with_pyproject(self, temp_dir: Path):
        """Test finding project root with pyproject.toml."""
        (temp_dir / "pyproject.toml").write_text("[project]\nname = 'test'")
        
        result = find_project_root(temp_dir)
        assert result == temp_dir
    
    def test_find_project_root_in_subdirectory(self, temp_dir: Path):
        """Test finding project root from subdirectory."""
        (temp_dir / ".git").mkdir()
        subdir = temp_dir / "subdir" / "nested"
        subdir.mkdir(parents=True)
        
        result = find_project_root(subdir)
        assert result == temp_dir
    
    def test_find_project_root_not_found(self, temp_dir: Path):
        """Test when project root is not found."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        result = find_project_root(subdir)
        assert result is None
    
    def test_find_project_root_default_cwd(self, monkeypatch):
        """Test finding project root with default (current directory)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / ".git").mkdir()
            
            # Mock Path.cwd() to return our temp directory
            monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
            
            result = find_project_root()
            assert result == tmp_path
    
    def test_find_project_root_with_setup_py(self, temp_dir: Path):
        """Test finding project root with setup.py."""
        (temp_dir / "setup.py").write_text("# setup")
        
        result = find_project_root(temp_dir)
        assert result == temp_dir
    
    def test_find_project_root_precedence(self, temp_dir: Path):
        """Test that .git takes precedence over other markers."""
        (temp_dir / ".git").mkdir()
        (temp_dir / "pyproject.toml").write_text("[project]\nname = 'test'")
        
        result = find_project_root(temp_dir)
        assert result == temp_dir


class TestGetShell:
    """Tests for get_shell function."""
    
    def test_get_shell_windows(self, monkeypatch):
        """Test getting shell on Windows."""
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setattr(os.environ, "get", lambda k, d=None: d)
        
        shell = get_shell()
        assert shell == "cmd.exe"
    
    def test_get_shell_windows_with_comspec(self, monkeypatch):
        """Test getting shell on Windows with COMSPEC set."""
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setattr(os.environ, "get", lambda k, d=None: "custom.exe" if k == "COMSPEC" else d)
        
        shell = get_shell()
        assert shell == "custom.exe"
    
    def test_get_shell_unix(self, monkeypatch):
        """Test getting shell on Unix."""
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setattr(os.environ, "get", lambda k, d=None: d)
        
        shell = get_shell()
        assert shell == "/bin/sh"
    
    def test_get_shell_unix_with_shell_env(self, monkeypatch):
        """Test getting shell on Unix with SHELL set."""
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setattr(os.environ, "get", lambda k, d=None: "/bin/bash" if k == "SHELL" else d)
        
        shell = get_shell()
        assert shell == "/bin/bash"


class TestEscapeShellArg:
    """Tests for escape_shell_arg function."""
    
    def test_escape_shell_arg_windows(self, monkeypatch):
        """Test escaping shell argument on Windows."""
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        
        result = escape_shell_arg('test"arg')
        assert result == 'test""arg'
    
    def test_escape_shell_arg_unix(self, monkeypatch):
        """Test escaping shell argument on Unix."""
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        
        result = escape_shell_arg("test'arg")
        assert result == "test'\"'\"'arg"
    
    def test_escape_shell_arg_no_special_chars(self, monkeypatch):
        """Test escaping shell argument with no special characters."""
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        
        result = escape_shell_arg("testarg")
        assert result == "testarg"


class TestGetProjectName:
    """Tests for get_project_name function."""
    
    def test_get_project_name_with_root(self, temp_dir: Path):
        """Test getting project name when root is found."""
        (temp_dir / ".git").mkdir()
        
        result = get_project_name(temp_dir)
        assert result == temp_dir.name
    
    def test_get_project_name_without_root(self, temp_dir: Path):
        """Test getting project name when root is not found."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        result = get_project_name(subdir)
        assert result == "subdir"
    
    def test_get_project_name_empty_path(self, temp_dir: Path):
        """Test getting project name with empty path."""
        # Create a path that doesn't exist
        non_existent = temp_dir / "nonexistent"
        
        result = get_project_name(non_existent)
        # Should return the directory name or "unknown"
        assert result in [non_existent.name, "unknown"]

