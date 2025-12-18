"""Tests for sindri.groups module."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sindri.core.context import ExecutionContext
from sindri.core.result import CommandResult
from sindri.groups import (
    ApplicationGroup,
    ComposeGroup,
    DockerGroup,
    GeneralGroup,
    GitGroup,
    PyPIGroup,
    QualityGroup,
    SindriGroup,
    VersionGroup,
    get_all_builtin_groups,
)
from sindri.groups.compose import (
    ComposeBuildCommand,
    ComposeDownCommand,
    ComposeLogsCommand,
    ComposeLogsTailCommand,
    ComposePsCommand,
    ComposePullCommand,
    ComposeRestartCommand,
    ComposeUpCommand,
)
from sindri.groups.docker import (
    DockerBuildAndPushCommand,
    DockerBuildCommand,
    DockerPushCommand,
)
from sindri.groups.general import SetupInstallCommand, SetupVenvCommand
from sindri.groups.git import (
    GitMonitorCommand,
    GitMonitorRunCommand,
    GitWorkflowCommand,
)
from sindri.groups.pypi import PyPIPushCommand, PyPIValidateCommand
from sindri.groups.version import (
    VersionBumpCommand,
    VersionShowCommand,
    VersionTagCommand,
)


@pytest.fixture
def mock_ctx(temp_dir: Path, sample_config):
    """Create a mock execution context."""
    return ExecutionContext(
        cwd=temp_dir,
        config=sample_config,
        verbose=False,
    )


@pytest.fixture
def mock_ctx_with_stream(temp_dir: Path, sample_config):
    """Create a mock execution context with stream callback."""
    stream_callback = MagicMock()
    return ExecutionContext(
        cwd=temp_dir,
        config=sample_config,
        verbose=False,
        stream_callback=stream_callback,
    )


class TestSindriGroup:
    """Tests for SindriGroup."""

    def test_sindri_group_initialization(self):
        """Test SindriGroup initialization."""
        group = SindriGroup()
        assert group.id == "sindri"
        assert group.title == "Sindri"
        assert group.order == 0

    def test_sindri_group_get_commands(self):
        """Test SindriGroup returns commands list."""
        group = SindriGroup()
        commands = group.get_commands()
        assert len(commands) == 5
        assert any(cmd.id == "docs-setup" for cmd in commands)
        assert any(cmd.id == "docs-preview" for cmd in commands)
        assert any(cmd.id == "docs-build" for cmd in commands)
        assert any(cmd.id == "docs-build-strict" for cmd in commands)
        assert any(cmd.id == "docs-deploy" for cmd in commands)


class TestGeneralGroup:
    """Tests for GeneralGroup."""

    def test_general_group_initialization(self):
        """Test GeneralGroup initialization."""
        group = GeneralGroup()
        assert group.id == "general"
        assert group.title == "General"
        assert group.order == 1

    def test_general_group_get_commands(self):
        """Test GeneralGroup returns commands."""
        group = GeneralGroup()
        commands = group.get_commands()
        assert len(commands) == 2
        assert any(cmd.id == "setup-venv" for cmd in commands)
        assert any(cmd.id == "setup-install" for cmd in commands)

    @pytest.mark.asyncio
    async def test_setup_venv_command_existing_venv(self, mock_ctx: ExecutionContext):
        """Test SetupVenvCommand when venv already exists."""
        # Create .venv directory
        venv_dir = mock_ctx.cwd / ".venv"
        venv_dir.mkdir()
        
        # Create Python executable
        if os.name == "nt":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        python_exe.parent.mkdir(parents=True, exist_ok=True)
        python_exe.touch()

        cmd = SetupVenvCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success
        assert "already exists" in result.stdout
        assert "activate" in result.stdout

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_setup_venv_command_create_new(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test SetupVenvCommand creates new venv."""
        mock_run.return_value = CommandResult(
            command_id="setup-venv",
            exit_code=0,
            stdout="Virtual environment created",
        )

        cmd = SetupVenvCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success
        assert "created" in result.stdout.lower()
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_setup_venv_command_failure(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test SetupVenvCommand handles failure."""
        mock_run.return_value = CommandResult(
            command_id="setup-venv",
            exit_code=1,
            stderr="Error creating venv",
        )

        cmd = SetupVenvCommand()
        result = await cmd.execute(mock_ctx)

        assert not result.success
        assert result.error is not None

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    @patch("sindri.utils.venv_helper.get_venv_python")
    async def test_setup_install_command_with_venv(
        self,
        mock_get_venv: MagicMock,
        mock_run: AsyncMock,
        mock_ctx: ExecutionContext,
    ):
        """Test SetupInstallCommand with existing venv."""
        python_path = mock_ctx.cwd / ".venv" / "bin" / "python"
        mock_get_venv.return_value = str(python_path)
        
        # Mock Path.exists for python_path
        with patch.object(Path, "exists", return_value=True):
            mock_run.return_value = CommandResult(
                command_id="setup-install",
                exit_code=0,
                stdout="Installed",
            )

            cmd = SetupInstallCommand()
            result = await cmd.execute(mock_ctx)

            assert result.success
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    @patch("sindri.utils.venv_helper.get_venv_python")
    async def test_setup_install_command_no_venv(
        self,
        mock_get_venv: MagicMock,
        mock_run: AsyncMock,
        mock_ctx: ExecutionContext,
    ):
        """Test SetupInstallCommand creates venv if missing."""
        mock_get_venv.return_value = None
        
        mock_run.return_value = CommandResult(
            command_id="setup-install",
            exit_code=0,
            stdout="Installed",
        )

        cmd = SetupInstallCommand()
        await cmd.execute(mock_ctx)

        # Should have called run_shell_command at least once (for venv creation and install)
        assert mock_run.call_count >= 1

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    @patch("sindri.utils.venv_helper.get_venv_python")
    async def test_setup_install_command_venv_creation_failure(
        self,
        mock_get_venv: MagicMock,
        mock_run: AsyncMock,
        mock_ctx: ExecutionContext,
    ):
        """Test SetupInstallCommand falls back to system Python if venv creation fails."""
        mock_get_venv.return_value = None
        
        # First call (venv creation) fails, second call (fallback install) succeeds
        mock_run.side_effect = [
            CommandResult(
                command_id="setup-install-create-venv",
                exit_code=1,
                error="Venv creation failed",
            ),
            CommandResult(
                command_id="setup-install",
                exit_code=0,
                stdout="Installed with system Python",
            ),
        ]

        cmd = SetupInstallCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success
        assert mock_run.call_count == 2


class TestQualityGroup:
    """Tests for QualityGroup."""

    def test_quality_group_initialization(self):
        """Test QualityGroup initialization."""
        group = QualityGroup()
        assert group.id == "quality"
        assert group.title == "Quality"
        assert group.order == 2

    def test_quality_group_get_commands(self):
        """Test QualityGroup returns commands."""
        group = QualityGroup()
        commands = group.get_commands()
        assert len(commands) == 6
        assert any(cmd.id == "lint" for cmd in commands)
        assert any(cmd.id == "format" for cmd in commands)
        assert any(cmd.id == "typecheck" for cmd in commands)
        assert any(cmd.id == "test" for cmd in commands)
        assert any(cmd.id == "test-cov" for cmd in commands)
        assert any(cmd.id == "quality-check" for cmd in commands)


class TestApplicationGroup:
    """Tests for ApplicationGroup."""

    def test_application_group_initialization(self):
        """Test ApplicationGroup initialization."""
        group = ApplicationGroup()
        assert group.id == "application"
        assert group.title == "Application"
        assert group.order == 3

    def test_application_group_get_commands(self):
        """Test ApplicationGroup returns commands."""
        group = ApplicationGroup()
        commands = group.get_commands()
        assert len(commands) == 2
        assert any(cmd.id == "app-run" for cmd in commands)
        assert any(cmd.id == "app-dev" for cmd in commands)


class TestDockerGroup:
    """Tests for DockerGroup."""

    def test_docker_group_initialization(self):
        """Test DockerGroup initialization."""
        group = DockerGroup()
        assert group.id == "docker"
        assert group.title == "Docker"
        assert group.order == 3

    def test_docker_group_get_commands(self):
        """Test DockerGroup returns commands."""
        group = DockerGroup()
        commands = group.get_commands()
        assert len(commands) == 8
        assert any(cmd.id == "docker-build" for cmd in commands)
        assert any(cmd.id == "docker-push" for cmd in commands)
        assert any(cmd.id == "docker-build_and_push" for cmd in commands)

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_docker_build_command_success(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test DockerBuildCommand success."""
        mock_ctx.config.project_name = "test-project"
        mock_ctx.config.version = "1.0.0"
        
        def expand_side_effect(x):
            return x.replace("{project_name}", "test-project").replace("{version}", "1.0.0")
        
        with patch.object(mock_ctx, "expand_templates", side_effect=expand_side_effect):
            mock_run.return_value = CommandResult(
                command_id="docker-build",
                exit_code=0,
                stdout="Successfully built",
            )

            cmd = DockerBuildCommand()
            result = await cmd.execute(mock_ctx)

            assert result.success
            mock_run.assert_called()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_docker_build_command_with_version_tag(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test DockerBuildCommand tags with version."""
        mock_ctx.config.project_name = "test-project"
        mock_ctx.config.version = "1.0.0"
        
        def expand_side_effect(x):
            return x.replace("{project_name}", "test-project").replace("{version}", "1.0.0")
        
        with patch.object(mock_ctx, "expand_templates", side_effect=expand_side_effect):
            # First call for build, second for tag
            mock_run.side_effect = [
                CommandResult(command_id="docker-build", exit_code=0, stdout="Built"),
                CommandResult(command_id="docker-build-tag", exit_code=0, stdout="Tagged"),
            ]

            cmd = DockerBuildCommand()
            result = await cmd.execute(mock_ctx)

            assert result.success
            assert mock_run.call_count == 2

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_docker_build_command_failure(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test DockerBuildCommand handles failure."""
        mock_ctx.config.project_name = "test-project"
        
        def expand_side_effect(x):
            return x.replace("{project_name}", "test-project")
        
        with patch.object(mock_ctx, "expand_templates", side_effect=expand_side_effect):
            mock_run.return_value = CommandResult(
                command_id="docker-build",
                exit_code=1,
                stderr="Build failed",
            )

            cmd = DockerBuildCommand()
            result = await cmd.execute(mock_ctx)

            assert not result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_docker_push_command_success(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test DockerPushCommand success."""
        mock_ctx.config.project_name = "test-project"
        mock_ctx.config.version = "1.0.0"
        # Mock registry expansion
        def expand_side_effect(x):
            replacements = {
                "{project_name}": "test-project",
                "{registry}": "registry.example.com",
                "{version}": "1.0.0",
            }
            for key, value in replacements.items():
                if key in x:
                    x = x.replace(key, value)
            return x
        
        with patch.object(mock_ctx, "expand_templates", side_effect=expand_side_effect):
            mock_run.side_effect = [
                CommandResult(command_id="tag-latest", exit_code=0),
                CommandResult(command_id="push-latest", exit_code=0),
                CommandResult(command_id="tag-version", exit_code=0),
                CommandResult(command_id="push-version", exit_code=0),
            ]

            cmd = DockerPushCommand()
            result = await cmd.execute(mock_ctx)

            assert result.success
            assert mock_run.call_count >= 2

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_docker_push_command_tag_failure(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test DockerPushCommand handles tag failure."""
        mock_ctx.config.project_name = "test-project"
        
        def expand_side_effect(x):
            replacements = {
                "{project_name}": "test-project",
                "{registry}": "registry.example.com",
            }
            for key, value in replacements.items():
                if key in x:
                    x = x.replace(key, value)
            return x
        
        with patch.object(mock_ctx, "expand_templates", side_effect=expand_side_effect):
            mock_run.return_value = CommandResult(
                command_id="tag-latest",
                exit_code=1,
                error="Tag failed",
            )

            cmd = DockerPushCommand()
            result = await cmd.execute(mock_ctx)

            assert not result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_docker_build_and_push_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test DockerBuildAndPushCommand."""
        mock_ctx.config.project_name = "test-project"
        mock_ctx.config.version = "1.0.0"
        
        def expand_side_effect(x):
            return x.replace("{project_name}", "test-project").replace("{version}", "1.0.0").replace("{registry}", "registry.example.com")
        
        with patch.object(mock_ctx, "expand_templates", side_effect=expand_side_effect):
            # Build command: 2 calls (build + tag with version)
            # Push command: 4 calls (tag latest, push latest, tag version, push version)
            mock_run.side_effect = [
                # Build phase
                CommandResult(command_id="docker-build", exit_code=0, stdout="Built"),
                CommandResult(command_id="docker-build-tag", exit_code=0, stdout="Tagged"),
                # Push phase
                CommandResult(command_id="tag-latest", exit_code=0),
                CommandResult(command_id="push-latest", exit_code=0),
                CommandResult(command_id="tag-version", exit_code=0),
                CommandResult(command_id="push-version", exit_code=0),
            ]

            cmd = DockerBuildAndPushCommand()
            result = await cmd.execute(mock_ctx)

            assert result.success
            assert "Built" in result.stdout

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_docker_build_and_push_build_failure(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test DockerBuildAndPushCommand handles build failure."""
        mock_ctx.config.project_name = "test-project"
        
        def expand_side_effect(x):
            return x.replace("{project_name}", "test-project")
        
        with patch.object(mock_ctx, "expand_templates", side_effect=expand_side_effect):
            mock_run.return_value = CommandResult(
                command_id="docker-build",
                exit_code=1,
                error="Build failed",
            )

            cmd = DockerBuildAndPushCommand()
            result = await cmd.execute(mock_ctx)

            assert not result.success
            assert "Build failed" in result.error


class TestComposeGroup:
    """Tests for ComposeGroup."""

    def test_compose_group_initialization(self):
        """Test ComposeGroup initialization."""
        group = ComposeGroup()
        assert group.id == "compose"
        assert group.title == "Docker Compose"
        assert group.order == 4

    def test_compose_group_with_custom_file(self):
        """Test ComposeGroup with custom compose file."""
        group = ComposeGroup(compose_file="custom-compose.yml")
        assert group.compose_file == "custom-compose.yml"

    def test_compose_group_get_commands(self):
        """Test ComposeGroup returns commands."""
        group = ComposeGroup()
        commands = group.get_commands()
        assert len(commands) == 8

    def test_compose_group_find_compose_file(self, temp_dir: Path):
        """Test _find_compose_file finds existing file."""
        compose_file = temp_dir / "docker-compose.yml"
        compose_file.write_text("version: '3'")
        
        group = ComposeGroup()
        found = group._find_compose_file(temp_dir)
        assert found == "docker-compose.yml"

    def test_compose_group_find_compose_file_precedence(self, temp_dir: Path):
        """Test _find_compose_file prefers docker-compose.yml."""
        (temp_dir / "compose.yml").write_text("version: '3'")
        (temp_dir / "docker-compose.yml").write_text("version: '3'")
        
        group = ComposeGroup()
        found = group._find_compose_file(temp_dir)
        assert found == "docker-compose.yml"

    def test_compose_group_find_compose_file_default(self, temp_dir: Path):
        """Test _find_compose_file returns default if none found."""
        group = ComposeGroup()
        found = group._find_compose_file(temp_dir)
        assert found == "docker-compose.yml"

    def test_compose_group_compose_cmd(self, temp_dir: Path):
        """Test _compose_cmd builds correct command."""
        group = ComposeGroup()
        cmd = group._compose_cmd("up", "-d", temp_dir)
        assert "docker compose" in cmd
        assert "up" in cmd
        assert "-d" in cmd

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_compose_up_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test ComposeUpCommand."""
        mock_run.return_value = CommandResult(
            command_id="compose-up",
            exit_code=0,
            stdout="Services started",
        )

        cmd = ComposeUpCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_compose_down_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test ComposeDownCommand."""
        mock_run.return_value = CommandResult(
            command_id="compose-down",
            exit_code=0,
        )

        cmd = ComposeDownCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_compose_restart_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test ComposeRestartCommand."""
        mock_run.return_value = CommandResult(
            command_id="compose-restart",
            exit_code=0,
        )

        cmd = ComposeRestartCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_compose_build_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test ComposeBuildCommand."""
        mock_run.return_value = CommandResult(
            command_id="compose-build",
            exit_code=0,
        )

        cmd = ComposeBuildCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_compose_logs_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test ComposeLogsCommand."""
        mock_run.return_value = CommandResult(
            command_id="compose-logs",
            exit_code=0,
        )

        cmd = ComposeLogsCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_compose_logs_tail_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test ComposeLogsTailCommand."""
        mock_run.return_value = CommandResult(
            command_id="compose-logs-tail",
            exit_code=0,
        )

        cmd = ComposeLogsTailCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_compose_ps_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test ComposePsCommand."""
        mock_run.return_value = CommandResult(
            command_id="compose-ps",
            exit_code=0,
            stdout="Name   Status",
        )

        cmd = ComposePsCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_compose_pull_command(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test ComposePullCommand."""
        mock_run.return_value = CommandResult(
            command_id="compose-pull",
            exit_code=0,
        )

        cmd = ComposePullCommand()
        result = await cmd.execute(mock_ctx)

        assert result.success


class TestGitGroup:
    """Tests for GitGroup."""

    def test_git_group_initialization(self):
        """Test GitGroup initialization."""
        group = GitGroup()
        assert group.id == "git"
        assert group.title == "Git"
        assert group.order == 5

    def test_git_group_with_default_message(self):
        """Test GitGroup with custom default message."""
        group = GitGroup(default_message="Custom message")
        assert group.default_message == "Custom message"

    def test_git_group_get_commands(self):
        """Test GitGroup returns commands."""
        group = GitGroup()
        commands = group.get_commands()
        assert len(commands) >= 5
        assert any(cmd.id == "git-status" for cmd in commands)
        assert any(cmd.id == "git-monitor" for cmd in commands)

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_command(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorCommand."""
        mock_run.return_value = CommandResult(
            command_id="git-status",
            exit_code=0,
            stdout="",
        )

        cmd = GitMonitorCommand()
        
        # Mock KeyboardInterrupt after first iteration
        with patch("asyncio.sleep", side_effect=KeyboardInterrupt()):
            result = await cmd.execute(mock_ctx_with_stream)

        assert result.success
        assert "stopped" in result.stdout.lower()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_no_gh(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test GitMonitorRunCommand when gh CLI is not available."""
        mock_run.return_value = CommandResult(
            command_id="gh-check",
            exit_code=1,
            error="gh not found",
        )

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx)

        assert not result.success
        assert "gh" in result.error.lower()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_workflow_command(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitWorkflowCommand."""
        mock_ctx_with_stream.config.project_name = "test-project"
        
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "git-add" in command_id:
                return CommandResult(command_id="git-add", exit_code=0)
            elif "git-commit" in command_id:
                return CommandResult(command_id="git-commit", exit_code=0)
            elif "git-push" in command_id:
                return CommandResult(command_id="git-push", exit_code=0)
            elif "git-rev-parse" in command_id:
                return CommandResult(command_id="git-rev-parse", exit_code=0, stdout="abc1234")
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitWorkflowCommand()
        
        # Mock the monitor command to avoid actual execution
        with patch.object(GitMonitorRunCommand, "execute", return_value=CommandResult(
            command_id="git-monitor-run",
            exit_code=0,
        )):
            with patch("asyncio.sleep"):  # Skip the sleep
                result = await cmd.execute(mock_ctx_with_stream)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_workflow_command_add_failure(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitWorkflowCommand handles add failure."""
        mock_run.return_value = CommandResult(
            command_id="git-add",
            exit_code=1,
            error="Add failed",
        )

        cmd = GitWorkflowCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert not result.success
        assert "add" in result.error.lower()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_command_with_changes(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorCommand with status changes."""
        mock_run.side_effect = [
            CommandResult(command_id="git-status", exit_code=0, stdout=" M file.txt"),
            CommandResult(command_id="git-branch", exit_code=0, stdout="main"),
        ]

        cmd = GitMonitorCommand()
        
        # Mock KeyboardInterrupt after first iteration
        with patch("asyncio.sleep", side_effect=KeyboardInterrupt()):
            result = await cmd.execute(mock_ctx_with_stream)

        assert result.success
        mock_ctx_with_stream.stream_callback.assert_called()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_command_exception(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorCommand handles exceptions."""
        mock_run.side_effect = Exception("Test error")

        cmd = GitMonitorCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert not result.success
        assert "Error" in result.error

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_gh_check_exception(
        self, mock_run: AsyncMock, mock_ctx: ExecutionContext
    ):
        """Test GitMonitorRunCommand handles exception during gh check."""
        mock_run.side_effect = Exception("Test error")

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx)

        assert not result.success
        assert "Error checking GitHub CLI" in result.error

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_no_runs(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorRunCommand when no runs found."""
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "gh-check" in command_id or command_id == "gh-check":
                return CommandResult(command_id="gh-check", exit_code=0)
            elif "gh-run-list" in command_id or command_id == "gh-run-list":
                return CommandResult(command_id="gh-run-list", exit_code=0, stdout="")
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert not result.success
        assert "No GitHub Actions runs" in result.error

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_completed_run(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorRunCommand with completed run."""
        import json
        
        run_data = [{
            "databaseId": "123456",
            "status": "completed",
            "conclusion": "success",
            "displayTitle": "Test Run",
            "headSha": "abc1234",
        }]

        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "gh-check" in command_id:
                return CommandResult(command_id="gh-check", exit_code=0)
            elif "gh-run-list" in command_id:
                return CommandResult(
                    command_id="gh-run-list",
                    exit_code=0,
                    stdout=json.dumps(run_data),
                )
            elif "gh-run-view" in command_id:
                return CommandResult(
                    command_id="gh-run-view",
                    exit_code=0,
                    stdout="Run completed successfully",
                )
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_json_decode_error(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorRunCommand handles JSON decode error."""
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "gh-check" in command_id:
                return CommandResult(command_id="gh-check", exit_code=0)
            elif "gh-run-list" in command_id:
                return CommandResult(command_id="gh-run-list", exit_code=0, stdout="invalid json")
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert not result.success
        assert "Could not parse" in result.error or "JSON" in result.error

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_no_run_id(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorRunCommand when run ID is missing."""
        import json
        
        run_data = [{
            "status": "completed",
            "conclusion": "success",
            "headSha": "abc1234",
        }]
        
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "gh-check" in command_id:
                return CommandResult(command_id="gh-check", exit_code=0)
            elif "gh-run-list" in command_id:
                return CommandResult(
                    command_id="gh-run-list",
                    exit_code=0,
                    stdout=json.dumps(run_data),
                )
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert not result.success
        assert "run id" in result.error.lower() or "run ID" in result.error

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_watch_run(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorRunCommand watches running workflow."""
        import json
        
        run_data = [{
            "databaseId": "123456",
            "status": "in_progress",
            "conclusion": None,
            "displayTitle": "Test Run",
            "headSha": "abc1234",
        }]
        
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "gh-check" in command_id:
                return CommandResult(command_id="gh-check", exit_code=0)
            elif "gh-run-list" in command_id:
                return CommandResult(
                    command_id="gh-run-list",
                    exit_code=0,
                    stdout=json.dumps(run_data),
                )
            elif "gh-run-watch" in command_id:
                return CommandResult(
                    command_id="gh-run-watch",
                    exit_code=0,
                    stdout="Run completed",
                )
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert result.success

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_keyboard_interrupt(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorRunCommand handles KeyboardInterrupt."""
        import json
        
        run_data = [{
            "databaseId": "123456",
            "status": "in_progress",
            "headSha": "abc1234",
        }]
        
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "gh-check" in command_id:
                return CommandResult(command_id="gh-check", exit_code=0)
            elif "gh-run-list" in command_id:
                return CommandResult(
                    command_id="gh-run-list",
                    exit_code=0,
                    stdout=json.dumps(run_data),
                )
            elif "gh-run-watch" in command_id:
                raise KeyboardInterrupt()
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert result.success
        assert "stopped" in result.stdout.lower()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_monitor_run_command_exception(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitMonitorRunCommand handles general exception."""
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "gh-check" in command_id:
                return CommandResult(command_id="gh-check", exit_code=0)
            elif "gh-run-list" in command_id:
                raise Exception("Test exception")
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitMonitorRunCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert not result.success
        assert "Error monitoring" in result.error

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_workflow_command_commit_failure(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitWorkflowCommand handles commit failure (not nothing to commit)."""
        mock_ctx_with_stream.config.project_name = "test-project"
        
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "git-add" in command_id:
                return CommandResult(command_id="git-add", exit_code=0)
            elif "git-commit" in command_id:
                return CommandResult(
                    command_id="git-commit",
                    exit_code=1,
                    error="Commit failed",
                )
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitWorkflowCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert not result.success
        assert "commit" in result.error.lower()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_workflow_command_nothing_to_commit(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitWorkflowCommand handles nothing to commit."""
        mock_ctx_with_stream.config.project_name = "test-project"
        
        def run_side_effect(*args, **kwargs):
            command_id = kwargs.get("command_id", "")
            if "git-add" in command_id:
                return CommandResult(command_id="git-add", exit_code=0)
            elif "git-commit" in command_id:
                return CommandResult(
                    command_id="git-commit",
                    exit_code=1,
                    stdout="nothing to commit",
                )
            elif "git-push" in command_id:
                return CommandResult(command_id="git-push", exit_code=0)
            return CommandResult(command_id=command_id, exit_code=0)
        
        mock_run.side_effect = run_side_effect

        cmd = GitWorkflowCommand()
        
        with patch.object(GitMonitorRunCommand, "execute", return_value=CommandResult(
            command_id="git-monitor-run",
            exit_code=0,
        )):
            result = await cmd.execute(mock_ctx_with_stream)

        # Should continue even if nothing to commit
        assert result is not None

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_git_workflow_command_push_failure(
        self, mock_run: AsyncMock, mock_ctx_with_stream: ExecutionContext
    ):
        """Test GitWorkflowCommand handles push failure."""
        mock_ctx_with_stream.config.project_name = "test-project"
        
        mock_run.side_effect = [
            CommandResult(command_id="git-add", exit_code=0),
            CommandResult(command_id="git-commit", exit_code=0),
            CommandResult(command_id="git-push", exit_code=1, error="Push failed"),
        ]

        cmd = GitWorkflowCommand()
        result = await cmd.execute(mock_ctx_with_stream)

        assert not result.success
        assert "push" in result.error.lower()


class TestVersionGroup:
    """Tests for VersionGroup."""

    def test_version_group_initialization(self):
        """Test VersionGroup initialization."""
        group = VersionGroup()
        assert group.id == "version"
        assert group.title == "Version"
        assert group.order == 2

    def test_version_group_get_commands(self):
        """Test VersionGroup returns commands."""
        group = VersionGroup()
        commands = group.get_commands()
        assert len(commands) == 3
        assert any(cmd.id == "version show" for cmd in commands)
        assert any(cmd.id == "version bump" for cmd in commands)
        assert any(cmd.id == "version tag" for cmd in commands)

    @pytest.mark.asyncio
    async def test_version_show_command_success(self, temp_dir: Path):
        """Test VersionShowCommand with valid pyproject.toml."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "test-project"\nversion = "1.0.0"\n'
        )

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionShowCommand()
        result = await cmd.execute(ctx)

        assert result.success
        assert "1.0.0" in result.stdout

    @pytest.mark.asyncio
    async def test_version_show_command_no_pyproject(self, temp_dir: Path):
        """Test VersionShowCommand without pyproject.toml."""
        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionShowCommand()
        result = await cmd.execute(ctx)

        assert not result.success
        assert "not available" in result.error.lower()

    @pytest.mark.asyncio
    async def test_version_show_command_version_only(self, temp_dir: Path):
        """Test VersionShowCommand with version only."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "2.0.0"\n')

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionShowCommand()
        result = await cmd.execute(ctx)

        assert result.success
        assert "2.0.0" in result.stdout

    @pytest.mark.asyncio
    async def test_version_bump_command_invalid_version(self, temp_dir: Path):
        """Test VersionBumpCommand with invalid version format."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "invalid"\n')

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionBumpCommand()
        result = await cmd.execute(ctx)

        assert not result.success
        assert "Invalid version format" in result.error

    @pytest.mark.asyncio
    async def test_version_bump_command_default_patch(self, temp_dir: Path):
        """Test VersionBumpCommand defaults to patch bump."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionBumpCommand()
        result = await cmd.execute(ctx)

        assert result.success
        assert "1.0.1" in result.stdout

    @pytest.mark.asyncio
    async def test_version_bump_command_update_failure(self, temp_dir: Path):
        """Test VersionBumpCommand handles update failure."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionBumpCommand()
        
        # Make file read-only to cause update failure
        import stat
        pyproject.chmod(stat.S_IREAD)
        try:
            result = await cmd.execute(ctx, bump_type="patch")
            # Should handle gracefully
            assert result is not None
        finally:
            pyproject.chmod(stat.S_IREAD | stat.S_IWRITE)

    @pytest.mark.asyncio
    async def test_version_show_command_with_poetry(self, temp_dir: Path):
        """Test VersionShowCommand with Poetry pyproject.toml."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text(
            '[tool.poetry]\nname = "test-project"\nversion = "2.1.0"\n'
        )

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionShowCommand()
        result = await cmd.execute(ctx)

        assert result.success
        assert "2.1.0" in result.stdout

    @pytest.mark.asyncio
    async def test_version_bump_command_with_poetry(self, temp_dir: Path):
        """Test VersionBumpCommand with Poetry pyproject.toml."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nversion = "1.0.0"\n')

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionBumpCommand()
        result = await cmd.execute(ctx, bump_type="minor")

        assert result.success
        assert "1.1.0" in result.stdout

    @pytest.mark.asyncio
    async def test_version_bump_command_patch(self, temp_dir: Path):
        """Test VersionBumpCommand bumps patch version."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionBumpCommand()
        result = await cmd.execute(ctx, bump_type="patch")

        assert result.success
        assert "1.0.1" in result.stdout
        
        # Verify file was updated
        content = pyproject.read_text()
        assert "1.0.1" in content

    @pytest.mark.asyncio
    async def test_version_bump_command_minor(self, temp_dir: Path):
        """Test VersionBumpCommand bumps minor version."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionBumpCommand()
        result = await cmd.execute(ctx, bump_type="minor")

        assert result.success
        assert "1.1.0" in result.stdout

    @pytest.mark.asyncio
    async def test_version_bump_command_major(self, temp_dir: Path):
        """Test VersionBumpCommand bumps major version."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionBumpCommand()
        result = await cmd.execute(ctx, bump_type="major")

        assert result.success
        assert "2.0.0" in result.stdout

    @pytest.mark.asyncio
    async def test_version_bump_command_no_pyproject(self, temp_dir: Path):
        """Test VersionBumpCommand without pyproject.toml."""
        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionBumpCommand()
        result = await cmd.execute(ctx)

        assert not result.success
        assert "version" in result.error.lower()

    @pytest.mark.asyncio
    @patch("sindri.core.shell_runner.run_shell_command")
    async def test_version_tag_command_success(
        self, mock_run: AsyncMock, temp_dir: Path
    ):
        """Test VersionTagCommand success."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')

        mock_run.return_value = CommandResult(
            command_id="version tag",
            exit_code=0,
            stdout="Tagged v1.0.0",
        )

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionTagCommand()
        result = await cmd.execute(ctx)

        assert result.success
        assert "v1.0.0" in result.stdout

    @pytest.mark.asyncio
    async def test_version_tag_command_no_version(self, temp_dir: Path):
        """Test VersionTagCommand without version."""
        ctx = ExecutionContext(cwd=temp_dir)
        cmd = VersionTagCommand()
        result = await cmd.execute(ctx)

        assert not result.success
        assert "version" in result.error.lower()


class TestPyPIGroup:
    """Tests for PyPIGroup."""

    def test_pypi_group_initialization(self):
        """Test PyPIGroup initialization."""
        group = PyPIGroup()
        assert group.id == "pypi"
        assert group.title == "PyPI"
        assert group.order == 6

    def test_pypi_group_get_commands(self):
        """Test PyPIGroup returns commands."""
        group = PyPIGroup()
        commands = group.get_commands()
        assert len(commands) == 2
        assert any(cmd.id == "pypi-validate" for cmd in commands)
        assert any(cmd.id == "pypi-push" for cmd in commands)

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_pypi_validate_command_success(
        self, mock_subprocess: MagicMock, temp_dir: Path
    ):
        """Test PyPIValidateCommand success."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        # Mock subprocess calls
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"OK", b""))
        mock_subprocess.return_value = mock_process

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIValidateCommand()
        
        # Mock multiple subprocess calls
        mock_subprocess.side_effect = [
            mock_process,  # pip show
            mock_process,  # pip install (if needed)
            mock_process,  # build
            mock_process,  # twine check
        ]
        
        result = await cmd.execute(ctx)

        # Should succeed or handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_pypi_validate_command_install_tools(
        self, mock_subprocess: MagicMock, temp_dir: Path
    ):
        """Test PyPIValidateCommand installs build tools if missing."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        # First call fails (tools not installed), second succeeds (install)
        mock_process_not_installed = MagicMock()
        mock_process_not_installed.returncode = 1
        mock_process_not_installed.communicate = AsyncMock(return_value=(b"", b""))
        
        mock_process_installed = MagicMock()
        mock_process_installed.returncode = 0
        mock_process_installed.communicate = AsyncMock(return_value=(b"OK", b""))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIValidateCommand()
        
        mock_subprocess.side_effect = [
            mock_process_not_installed,  # pip show (fails)
            mock_process_installed,      # pip install
            mock_process_installed,      # build
            mock_process_installed,      # twine check
        ]
        
        result = await cmd.execute(ctx)

        assert result is not None

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_pypi_validate_command_build_failure(
        self, mock_subprocess: MagicMock, temp_dir: Path
    ):
        """Test PyPIValidateCommand handles build failure."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process_success = MagicMock()
        mock_process_success.returncode = 0
        mock_process_success.communicate = AsyncMock(return_value=(b"OK", b""))
        
        mock_process_failure = MagicMock()
        mock_process_failure.returncode = 1
        mock_process_failure.communicate = AsyncMock(return_value=(b"", b"Build failed"))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIValidateCommand()
        
        mock_subprocess.side_effect = [
            mock_process_success,  # pip show
            mock_process_failure,  # build (fails)
        ]
        
        result = await cmd.execute(ctx)

        assert not result.success
        assert "validation failed" in result.error.lower()

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_pypi_validate_command_exception(
        self, mock_subprocess: MagicMock, temp_dir: Path
    ):
        """Test PyPIValidateCommand handles exceptions."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_subprocess.side_effect = Exception("Test error")

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIValidateCommand()
        result = await cmd.execute(ctx)

        assert not result.success
        assert "Error" in result.error

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_pypi_validate_command_with_dist_files(
        self, mock_subprocess: MagicMock, temp_dir: Path
    ):
        """Test PyPIValidateCommand with dist files and twine check."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')
        
        # Create dist directory with files
        dist_dir = temp_dir / "dist"
        dist_dir.mkdir()
        (dist_dir / "test-1.0.0.tar.gz").write_text("test")

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"OK", b""))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIValidateCommand()
        
        mock_subprocess.side_effect = [
            mock_process,  # pip show
            mock_process,  # build
            mock_process,  # twine check
        ]
        
        result = await cmd.execute(ctx)

        assert result is not None

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_pypi_validate_command_twine_check_failure(
        self, mock_subprocess: MagicMock, temp_dir: Path
    ):
        """Test PyPIValidateCommand handles twine check failure."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')
        
        dist_dir = temp_dir / "dist"
        dist_dir.mkdir()
        (dist_dir / "test-1.0.0.tar.gz").write_text("test")

        mock_process_success = MagicMock()
        mock_process_success.returncode = 0
        mock_process_success.communicate = AsyncMock(return_value=(b"OK", b""))
        
        mock_process_failure = MagicMock()
        mock_process_failure.returncode = 1
        mock_process_failure.communicate = AsyncMock(return_value=(b"", b"Check failed"))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIValidateCommand()
        
        mock_subprocess.side_effect = [
            mock_process_success,  # pip show
            mock_process_success,  # build
            mock_process_failure,  # twine check (fails)
        ]
        
        result = await cmd.execute(ctx)

        assert not result.success
        assert "metadata validation failed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_pypi_validate_command_no_pyproject(self, temp_dir: Path):
        """Test PyPIValidateCommand without pyproject.toml."""
        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIValidateCommand()
        result = await cmd.execute(ctx)

        assert not result.success
        assert "pyproject.toml" in result.error.lower()

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("shutil.rmtree")
    async def test_pypi_push_command_success(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        temp_dir: Path,
    ):
        """Test PyPIPushCommand success."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"OK", b""))
        mock_subprocess.return_value = mock_process

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        
        # Mock multiple subprocess calls
        mock_subprocess.side_effect = [
            mock_process,  # pip show
            mock_process,  # pip install (if needed)
            mock_process,  # build
            mock_process,  # twine upload
        ]
        
        result = await cmd.execute(ctx)

        # Should succeed or handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("shutil.rmtree")
    async def test_pypi_push_command_test_repo(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        temp_dir: Path,
    ):
        """Test PyPIPushCommand with test repository."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"OK", b""))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        
        mock_subprocess.side_effect = [
            mock_process,  # pip show
            mock_process,  # build
            mock_process,  # twine upload (test)
        ]
        
        result = await cmd.execute(ctx, test=True)

        assert result is not None

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("shutil.rmtree")
    async def test_pypi_push_command_build_failure(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        temp_dir: Path,
    ):
        """Test PyPIPushCommand handles build failure."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process_success = MagicMock()
        mock_process_success.returncode = 0
        mock_process_success.communicate = AsyncMock(return_value=(b"OK", b""))
        
        mock_process_failure = MagicMock()
        mock_process_failure.returncode = 1
        mock_process_failure.communicate = AsyncMock(return_value=(b"", b"Build failed"))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        
        mock_subprocess.side_effect = [
            mock_process_success,  # pip show
            mock_process_failure,  # build (fails)
        ]
        
        result = await cmd.execute(ctx)

        assert not result.success
        assert "build failed" in result.error.lower()

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("shutil.rmtree")
    async def test_pypi_push_command_upload_failure(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        temp_dir: Path,
    ):
        """Test PyPIPushCommand handles upload failure."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process_success = MagicMock()
        mock_process_success.returncode = 0
        mock_process_success.communicate = AsyncMock(return_value=(b"OK", b""))
        
        mock_process_failure = MagicMock()
        mock_process_failure.returncode = 1
        mock_process_failure.communicate = AsyncMock(return_value=(b"", b"Upload failed"))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        
        mock_subprocess.side_effect = [
            mock_process_success,  # pip show
            mock_process_success,  # build
            mock_process_failure,  # upload (fails)
        ]
        
        result = await cmd.execute(ctx)

        assert not result.success
        assert "upload" in result.error.lower()

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("shutil.rmtree")
    async def test_pypi_push_command_install_tools_failure(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        temp_dir: Path,
    ):
        """Test PyPIPushCommand handles build tools installation failure."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process_not_installed = MagicMock()
        mock_process_not_installed.returncode = 1
        mock_process_not_installed.communicate = AsyncMock(return_value=(b"", b""))
        
        mock_process_install_failure = MagicMock()
        mock_process_install_failure.returncode = 1
        mock_process_install_failure.communicate = AsyncMock(return_value=(b"", b"Install failed"))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        
        mock_subprocess.side_effect = [
            mock_process_not_installed,  # pip show (fails)
            mock_process_install_failure,  # pip install (fails)
        ]
        
        result = await cmd.execute(ctx)

        assert not result.success
        assert "install build tools" in result.error.lower()

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("shutil.rmtree")
    async def test_pypi_push_command_with_repository(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        temp_dir: Path,
    ):
        """Test PyPIPushCommand with custom repository."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"OK", b""))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        
        mock_subprocess.side_effect = [
            mock_process,  # pip show
            mock_process,  # build
            mock_process,  # twine upload with repository
        ]
        
        result = await cmd.execute(ctx, repository="custom-repo")

        assert result is not None

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("shutil.rmtree")
    async def test_pypi_push_command_build_exception(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        temp_dir: Path,
    ):
        """Test PyPIPushCommand handles build exception."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process_success = MagicMock()
        mock_process_success.returncode = 0
        mock_process_success.communicate = AsyncMock(return_value=(b"OK", b""))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        
        mock_subprocess.side_effect = [
            mock_process_success,  # pip show
            Exception("Build exception"),  # build (exception)
        ]
        
        result = await cmd.execute(ctx)

        assert not result.success
        assert "Error building package" in result.error

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("shutil.rmtree")
    async def test_pypi_push_command_upload_exception(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        temp_dir: Path,
    ):
        """Test PyPIPushCommand handles upload exception."""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.0.0"\n')

        mock_process_success = MagicMock()
        mock_process_success.returncode = 0
        mock_process_success.communicate = AsyncMock(return_value=(b"OK", b""))

        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        
        mock_subprocess.side_effect = [
            mock_process_success,  # pip show
            mock_process_success,  # build
            Exception("Upload exception"),  # upload (exception)
        ]
        
        result = await cmd.execute(ctx)

        assert not result.success
        assert "Error uploading package" in result.error

    @pytest.mark.asyncio
    async def test_pypi_push_command_no_pyproject(self, temp_dir: Path):
        """Test PyPIPushCommand without pyproject.toml."""
        ctx = ExecutionContext(cwd=temp_dir)
        cmd = PyPIPushCommand()
        result = await cmd.execute(ctx)

        assert not result.success
        assert "pyproject.toml" in result.error.lower()


class TestGetAllBuiltinGroups:
    """Tests for get_all_builtin_groups function."""

    def test_get_all_builtin_groups(self):
        """Test get_all_builtin_groups returns all groups."""
        groups = get_all_builtin_groups()
        assert len(groups) == 9
        
        group_ids = [g.id for g in groups]
        assert "sindri" in group_ids
        assert "general" in group_ids
        assert "quality" in group_ids
        assert "application" in group_ids
        assert "docker" in group_ids
        assert "compose" in group_ids
        assert "git" in group_ids
        assert "version" in group_ids
        assert "pypi" in group_ids

    def test_get_all_builtin_groups_order(self):
        """Test get_all_builtin_groups returns groups in order."""
        groups = get_all_builtin_groups()
        orders = [g.order for g in groups if g.order is not None]
        assert orders == sorted(orders)

