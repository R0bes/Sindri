"""Docker command group."""

from pathlib import Path
from typing import Any, Dict, Optional

from sindri.commands.command import Command
from sindri.commands.group import CommandGroup
from sindri.commands.shell_command import ShellCommand
from sindri.runner import AsyncExecutionEngine, CommandResult
from sindri.utils.helper import (
    get_project_name,
    get_project_version_from_pyproject,
)


class BuildCommand(Command):
    """Command that builds Docker image with multiple tags."""

    def __init__(
        self,
        command_id: str,
        project_name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize build command.

        Args:
            command_id: Unique identifier for the command
            project_name: Project name for image naming
            title: Display title (defaults to command_id)
            description: Command description
        """
        super().__init__(
            command_id,
            title or "Build",
            description or "Build Docker image with tags",
        )
        self.project_name = project_name

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """
        Execute build command with version tag.

        Args:
            engine: Execution engine instance
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional arguments

        Returns:
            CommandResult with execution details
        """
        # Get version from pyproject.toml
        version = get_project_version_from_pyproject(cwd)
        if not version:
            version = "latest"

        # Build commands
        local_name = self.project_name
        local_latest = f"{self.project_name}:latest"
        local_version = f"{self.project_name}:{version}"

        from sindri.config import Command as ConfigCommand

        # Build with both tags
        build_cmd = ConfigCommand(
            id=self.command_id,
            title=self.title,
            description=self.description,
            shell=(
                f"docker build -t {local_name} "
                f"-t {local_latest} ."
            ),
        )

        stream_callback = kwargs.get("stream_callback")
        build_result = await engine.run_command(build_cmd, stream_callback)

        if not build_result.success:
            return build_result

        # Tag with version if version is not "latest"
        if version != "latest":
            tag_cmd = ConfigCommand(
                id=f"{self.command_id}-tag",
                shell=f"docker tag {local_latest} {local_version}",
            )
            tag_result = await engine.run_command(tag_cmd, stream_callback)
            # Combine results
            combined_stdout = (
                f"{build_result.stdout}\n{tag_result.stdout}".strip()
            )
            combined_stderr = (
                f"{build_result.stderr}\n{tag_result.stderr}".strip()
            )
            return CommandResult(
                self.command_id,
                tag_result.exit_code,
                stdout=combined_stdout,
                stderr=combined_stderr,
                duration=build_result.duration + tag_result.duration,
            )

        return build_result


class PushCommand(Command):
    """Command that pushes Docker image to registry with multiple tags."""

    def __init__(
        self,
        command_id: str,
        project_name: str,
        registry: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize push command.

        Args:
            command_id: Unique identifier for the command
            project_name: Project name for image naming
            registry: Docker registry URL
            title: Display title (defaults to command_id)
            description: Command description
        """
        super().__init__(
            command_id,
            title or "Push",
            description or "Push Docker image to registry",
        )
        self.project_name = project_name
        self.registry = registry

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """
        Execute push command with version tag.

        Args:
            engine: Execution engine instance
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional arguments

        Returns:
            CommandResult with execution details
        """
        # Get version from pyproject.toml
        version = get_project_version_from_pyproject(cwd)
        if not version:
            version = "latest"

        local_latest = f"{self.project_name}:latest"
        registry_latest = f"{self.registry}/{self.project_name}:latest"
        registry_version = f"{self.registry}/{self.project_name}:{version}"

        from sindri.config import Command as ConfigCommand

        stream_callback = kwargs.get("stream_callback")
        results = []

        # Tag and push latest
        tag_latest_cmd = ConfigCommand(
            id=f"{self.command_id}-tag-latest",
            shell=f"docker tag {local_latest} {registry_latest}",
        )
        results.append(
            await engine.run_command(tag_latest_cmd, stream_callback)
        )

        # Tag and push version (if not latest)
        if version != "latest":
            tag_version_cmd = ConfigCommand(
                id=f"{self.command_id}-tag-version",
                shell=f"docker tag {local_latest} {registry_version}",
            )
            results.append(
                await engine.run_command(tag_version_cmd, stream_callback)
            )

        # Push latest
        push_latest_cmd = ConfigCommand(
            id=f"{self.command_id}-push-latest",
            shell=f"docker push {registry_latest}",
        )
        results.append(
            await engine.run_command(push_latest_cmd, stream_callback)
        )

        # Push version (if not latest)
        if version != "latest":
            push_version_cmd = ConfigCommand(
                id=f"{self.command_id}-push-version",
                shell=f"docker push {registry_version}",
            )
            results.append(
                await engine.run_command(push_version_cmd, stream_callback)
            )

        # Combine results
        all_success = all(r.success for r in results)
        combined_stdout = (
            "\n".join(r.stdout for r in results if r.stdout).strip()
        )
        combined_stderr = (
            "\n".join(r.stderr for r in results if r.stderr).strip()
        )
        total_duration = sum(r.duration for r in results)
        error = (
            None if all_success else "One or more push operations failed"
        )

        return CommandResult(
            self.command_id,
            0 if all_success else 1,
            stdout=combined_stdout,
            stderr=combined_stderr,
            error=error,
            duration=total_duration,
        )


class BuildAndPushCommand(Command):
    """Command that executes build and push commands sequentially."""

    def __init__(
        self,
        command_id: str,
        build_command_id: str,
        push_command_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize build and push command.

        Args:
            command_id: Unique identifier for the command
            build_command_id: ID of the build command to run first
            push_command_id: ID of the push command to run after build
            title: Display title (defaults to command_id)
            description: Command description
        """
        super().__init__(
            command_id,
            title or "Build and Push",
            description or "Build and push Docker image to registry",
        )
        self.build_command_id = build_command_id
        self.push_command_id = push_command_id

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """
        Execute build and push commands sequentially.

        Args:
            engine: Execution engine instance
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional arguments

        Returns:
            CommandResult with execution details
        """
        # Get all commands from the engine's config
        if not engine.config:
            return CommandResult(
                self.command_id,
                1,
                error="No config available to find commands",
            )

        # Find build and push commands
        all_commands = engine.config.commands
        build_cmd = next(
            (
                cmd
                for cmd in all_commands
                if cmd.primary_id == self.build_command_id
            ),
            None,
        )
        push_cmd = next(
            (
                cmd
                for cmd in all_commands
                if cmd.primary_id == self.push_command_id
            ),
            None,
        )

        if not build_cmd:
            return CommandResult(
                self.command_id,
                1,
                error=(
                    f"Build command '{self.build_command_id}' not found"
                ),
            )
        if not push_cmd:
            return CommandResult(
                self.command_id,
                1,
                error=(
                    f"Push command '{self.push_command_id}' not found"
                ),
            )

        # Run build command first
        stream_callback = kwargs.get("stream_callback")
        build_result = await engine.run_command(build_cmd, stream_callback)

        # If build failed, return early
        if not build_result.success:
            return CommandResult(
                self.command_id,
                build_result.exit_code,
                stdout=build_result.stdout,
                stderr=build_result.stderr,
                error=f"Build failed: {build_result.error or 'Unknown error'}",
                duration=build_result.duration,
            )

        # Run push command after successful build
        push_result = await engine.run_command(push_cmd, stream_callback)

        # Combine results
        combined_stdout = (
            f"{build_result.stdout}\n{push_result.stdout}"
            if build_result.stdout or push_result.stdout
            else ""
        )
        combined_stderr = (
            f"{build_result.stderr}\n{push_result.stderr}"
            if build_result.stderr or push_result.stderr
            else ""
        )

        return CommandResult(
            self.command_id,
            push_result.exit_code,
            stdout=combined_stdout.strip() if combined_stdout else "",
            stderr=combined_stderr.strip() if combined_stderr else "",
            error=push_result.error,
            duration=build_result.duration + push_result.duration,
        )


class DockerGroup(CommandGroup):
    """
    Docker command group with shared logic for Docker operations.

    Provides common functionality for Docker commands like registry handling
    and container name resolution.
    """

    def __init__(
        self,
        registry: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        """
        Initialize Docker command group.

        Args:
            registry: Docker registry URL (defaults to global default)
            project_name: Project name for container/image naming
        """
        super().__init__(
            group_id="docker",
            title="Docker",
            description="Docker container and image commands",
            order=3,
        )
        self.registry = registry or "registry.schwende.lan:5000"
        # Derive project name from current directory if not provided
        if project_name:
            self.project_name = project_name
        else:
            # Try to get project name from current working directory
            try:
                cwd = Path.cwd()
                self.project_name = get_project_name(cwd)
            except (OSError, ValueError):
                # Fallback to default if we can't determine project name
                self.project_name = "my-project"
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _get_image_name(self, tag: str = "latest") -> str:
        """Get full image name with registry and tag."""
        return f"{self.registry}/{self.project_name}:{tag}"

    def _get_local_image_name(self, tag: str = "latest") -> str:
        """Get local image name without registry."""
        return f"{self.project_name}:{tag}"

    def _get_container_name(self) -> str:
        """Get container name based on project name."""
        return self.project_name

    def _initialize_commands(self) -> None:
        """Initialize Docker commands."""
        container_name = self._get_container_name()

        self._command_list = [
            ShellCommand(
                command_id="docker-restart",
                shell=(
                    f"docker restart "
                    f"$(docker ps -q --filter 'name={container_name}') "
                    "|| echo 'No container running'"
                ),
                title="Rebuild+Restart",
                description="Restart Docker container",
            ),
            ShellCommand(
                command_id="docker-re",
                shell=(
                    f"docker restart "
                    f"$(docker ps -q --filter 'name={container_name}') "
                    "|| echo 'No container running'"
                ),
                title="Rebuild+Restart",
                description="Restart Docker container (alias)",
            ),
            ShellCommand(
                command_id="docker-up",
                shell=(
                    f"docker run -d --name {container_name} "
                    f"{self._get_image_name()} "
                    f"|| docker start {container_name}"
                ),
                title="Up",
                description="Start Docker container",
            ),

            ShellCommand(
                command_id="docker-down",
                shell=(
                    f"docker stop {container_name} "
                    "|| echo 'Container not running'"
                ),
                title="Down",
                description="Stop Docker container",
            ),
            BuildCommand(
                command_id="docker-build",
                project_name=self.project_name,
            ),
            PushCommand(
                command_id="docker-push",
                project_name=self.project_name,
                registry=self.registry,
            ),
            BuildAndPushCommand(
                command_id="docker-build_and_push",
                build_command_id="docker-build",
                push_command_id="docker-push",
            ),

        ]

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list
