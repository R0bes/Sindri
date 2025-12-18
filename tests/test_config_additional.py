"""Additional tests for configuration functions."""

from pathlib import Path

from sindri.config import (
    Command,
    Group,
    SindriConfig,
    load_config,
    load_global_defaults,
    load_project_environments,
)


class TestGetEnvVars:
    """Tests for get_env_vars method."""
    
    def test_get_env_vars_dev(self, temp_dir: Path):
        """Test getting dev environment variables."""
        # Create project config
        project_config_dir = temp_dir / ".sindri"
        project_config_dir.mkdir()
        project_config = project_config_dir / "config.toml"
        project_config.write_text("""[environments.dev]
NODE_ENV = "development"
API_URL = "http://localhost:3000"
""")
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "test"
shell = "echo test"
""")
        
        config = load_config(config_path=config_file)
        env_vars = config.get_env_vars("dev")
        
        assert "NODE_ENV" in env_vars
        assert env_vars["NODE_ENV"] == "development"
        assert env_vars["API_URL"] == "http://localhost:3000"
    
    def test_get_env_vars_test(self, temp_dir: Path):
        """Test getting test environment variables."""
        project_config_dir = temp_dir / ".sindri"
        project_config_dir.mkdir()
        project_config = project_config_dir / "config.toml"
        project_config.write_text("""[environments.test]
NODE_ENV = "test"
API_URL = "http://test.example.com"
""")
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "test"
shell = "echo test"
""")
        
        config = load_config(config_path=config_file)
        env_vars = config.get_env_vars("test")
        
        assert env_vars["NODE_ENV"] == "test"
        assert env_vars["API_URL"] == "http://test.example.com"
    
    def test_get_env_vars_prod(self, temp_dir: Path):
        """Test getting prod environment variables."""
        project_config_dir = temp_dir / ".sindri"
        project_config_dir.mkdir()
        project_config = project_config_dir / "config.toml"
        project_config.write_text("""[environments.prod]
NODE_ENV = "production"
API_URL = "https://api.example.com"
""")
        
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "test"
shell = "echo test"
""")
        
        config = load_config(config_path=config_file)
        env_vars = config.get_env_vars("prod")
        
        assert env_vars["NODE_ENV"] == "production"
        assert env_vars["API_URL"] == "https://api.example.com"
    
    def test_get_env_vars_no_project_config(self, temp_dir: Path):
        """Test getting env vars when no project config exists."""
        config_file = temp_dir / "sindri.toml"
        config_file.write_text("""version = "1.0"
[[commands]]
id = "test"
shell = "echo test"
""")
        
        config = load_config(config_path=config_file)
        env_vars = config.get_env_vars("dev")
        
        assert env_vars == {}


class TestGetCommandsOrganizedByGroups:
    """Tests for get_commands_organized_by_groups method."""
    
    def test_get_commands_organized_no_groups(self):
        """Test organizing commands when no groups are defined."""
        config = SindriConfig(
            commands=[
                Command(id="cmd1", shell="echo 1"),
                Command(id="cmd2", shell="echo 2"),
            ]
        )
        
        organized = config.get_commands_organized_by_groups()
        
        assert len(organized) == 1
        assert organized[0][0] is None  # No group
        assert len(organized[0][1]) == 2
    
    def test_get_commands_organized_with_groups(self):
        """Test organizing commands with groups."""
        config = SindriConfig(
            commands=[
                Command(id="cmd1", shell="echo 1"),
                Command(id="cmd2", shell="echo 2"),
                Command(id="cmd3", shell="echo 3"),
            ],
            groups=[
                Group(id="group1", title="Group 1", order=1, commands=["cmd1", "cmd2"]),
            ]
        )
        
        organized = config.get_commands_organized_by_groups()
        
        assert len(organized) == 2  # One group + ungrouped
        assert organized[0][0] is not None
        assert organized[0][0].id == "group1"
        assert len(organized[0][1]) == 2
        assert organized[1][0] is None  # Ungrouped
        assert len(organized[1][1]) == 1
    
    def test_get_commands_organized_sorted_by_order(self):
        """Test that groups are sorted by order."""
        config = SindriConfig(
            commands=[
                Command(id="cmd1", shell="echo 1"),
                Command(id="cmd2", shell="echo 2"),
                Command(id="cmd3", shell="echo 3"),
            ],
            groups=[
                Group(id="group2", title="Group 2", order=2, commands=["cmd2"]),
                Group(id="group1", title="Group 1", order=1, commands=["cmd1"]),
            ]
        )
        
        organized = config.get_commands_organized_by_groups()
        
        assert len(organized) == 3  # Two groups + ungrouped cmd3
        assert organized[0][0].id == "group1"  # Order 1 first
        assert organized[1][0].id == "group2"  # Order 2 second
        assert organized[2][0] is None  # Ungrouped cmd3
    
    def test_get_commands_organized_with_missing_command(self):
        """Test organizing when group references non-existent command."""
        config = SindriConfig(
            commands=[
                Command(id="cmd1", shell="echo 1"),
            ],
            groups=[
                Group(id="group1", title="Group 1", order=1, commands=["cmd1", "nonexistent"]),
            ]
        )
        
        organized = config.get_commands_organized_by_groups()
        
        assert len(organized) == 1
        assert len(organized[0][1]) == 1  # Only cmd1, nonexistent is ignored


class TestLoadGlobalDefaults:
    """Tests for load_global_defaults function."""
    
    def test_load_global_defaults_not_exists(self, monkeypatch, tmp_path: Path):
        """Test loading global defaults when file doesn't exist."""
        # Mock home directory
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        
        def mock_home_func():
            return mock_home
        
        monkeypatch.setattr("pathlib.Path.home", mock_home_func)
        
        defaults = load_global_defaults()
        
        assert defaults.docker_registry == "registry.schwende.lan:5000"
    
    def test_load_global_defaults_exists(self, monkeypatch, tmp_path: Path):
        """Test loading global defaults from existing file."""
        # Create global config
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        sindri_dir = mock_home / ".sindri"
        sindri_dir.mkdir()
        global_config = sindri_dir / "config.toml"
        global_config.write_text("""[defaults]
docker_registry = "custom.registry:5000"
""")
        
        def mock_home_func():
            return mock_home
        
        monkeypatch.setattr("pathlib.Path.home", mock_home_func)
        
        defaults = load_global_defaults()
        
        assert defaults.docker_registry == "custom.registry:5000"


class TestLoadProjectEnvironments:
    """Tests for load_project_environments function."""
    
    def test_load_project_environments_not_exists(self, temp_dir: Path):
        """Test loading project environments when file doesn't exist."""
        envs = load_project_environments(temp_dir)
        
        assert envs.dev is None
        assert envs.test is None
        assert envs.prod is None
    
    def test_load_project_environments_exists(self, temp_dir: Path):
        """Test loading project environments from existing file."""
        # Create project config
        project_config_dir = temp_dir / ".sindri"
        project_config_dir.mkdir()
        project_config = project_config_dir / "config.toml"
        project_config.write_text("""[environments.dev]
NODE_ENV = "development"

[environments.prod]
NODE_ENV = "production"
""")
        
        envs = load_project_environments(temp_dir)
        
        assert envs.dev is not None
        assert envs.dev["NODE_ENV"] == "development"
        assert envs.prod is not None
        assert envs.prod["NODE_ENV"] == "production"
        assert envs.test is None

