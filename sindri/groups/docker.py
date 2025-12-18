"""Docker command group - container and image management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sindri.core.command import CustomCommand, ShellCommand
from sindri.core.group import CommandGroup
from sindri.core.result import CommandResult

if TYPE_CHECKING:
    from sindri.core.context import ExecutionContext


class DockerBuildCommand(CustomCommand):
    """Build Docker image with automatic version tagging."""

    def __init__(self) -> None:
        super().__init__(
            command_id="docker-build",
            title="Build",
            description="Build Docker image with latest and version tags",
            group_id="docker",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Build Docker image with multiple tags."""
        from sindri.core.shell_runner import run_shell_command

        project_name = ctx.expand_templates("{project_name}")
        version = ctx.expand_templates("{version}")

        # Build with latest tag
        build_shell = f"docker build -t {project_name}:latest ."

        result = await run_shell_command(
            command_id=self.id,
            shell=build_shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )

        if not result.success:
            return result

        # Tag with version if available
        if version and version != "latest":
            tag_shell = f"docker tag {project_name}:latest {project_name}:{version}"
            tag_result = await run_shell_command(
                command_id=f"{self.id}-tag",
                shell=tag_shell,
                cwd=ctx.cwd,
                env=ctx.get_env(),
                stream_callback=ctx.stream_callback,
            )

            return CommandResult(
                command_id=self.id,
                exit_code=tag_result.exit_code,
                stdout=f"{result.stdout}\n{tag_result.stdout}".strip(),
                stderr=f"{result.stderr}\n{tag_result.stderr}".strip(),
                duration=(result.duration or 0) + (tag_result.duration or 0),
            )

        return result


class DockerPushCommand(CustomCommand):
    """Push Docker image to registry with version tags."""

    def __init__(self) -> None:
        super().__init__(
            command_id="docker-push",
            title="Push",
            description="Push Docker image to registry",
            group_id="docker",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Push Docker image with multiple tags."""
        from sindri.core.shell_runner import run_shell_command

        project_name = ctx.expand_templates("{project_name}")
        registry = ctx.expand_templates("{registry}")
        version = ctx.expand_templates("{version}")

        results = []
        total_duration = 0.0

        # Tag and push latest
        registry_latest = f"{registry}/{project_name}:latest"

        tag_latest = await run_shell_command(
            command_id=f"{self.id}-tag-latest",
            shell=f"docker tag {project_name}:latest {registry_latest}",
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )
        results.append(tag_latest)
        total_duration += tag_latest.duration or 0

        if not tag_latest.success:
            return CommandResult(
                command_id=self.id,
                exit_code=tag_latest.exit_code,
                error="Failed to tag image for registry",
            )

        push_latest = await run_shell_command(
            command_id=f"{self.id}-push-latest",
            shell=f"docker push {registry_latest}",
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )
        results.append(push_latest)
        total_duration += push_latest.duration or 0

        if not push_latest.success:
            return CommandResult(
                command_id=self.id,
                exit_code=push_latest.exit_code,
                error="Failed to push latest tag",
            )

        # Tag and push version if available
        if version and version != "latest":
            registry_version = f"{registry}/{project_name}:{version}"

            tag_version = await run_shell_command(
                command_id=f"{self.id}-tag-version",
                shell=f"docker tag {project_name}:latest {registry_version}",
                cwd=ctx.cwd,
                env=ctx.get_env(),
                stream_callback=ctx.stream_callback,
            )
            results.append(tag_version)
            total_duration += tag_version.duration or 0

            push_version = await run_shell_command(
                command_id=f"{self.id}-push-version",
                shell=f"docker push {registry_version}",
                cwd=ctx.cwd,
                env=ctx.get_env(),
                stream_callback=ctx.stream_callback,
            )
            results.append(push_version)
            total_duration += push_version.duration or 0

        # Combine results
        all_success = all(r.success for r in results)
        stdout = "\n".join(r.stdout for r in results if r.stdout).strip()
        stderr = "\n".join(r.stderr for r in results if r.stderr).strip()

        return CommandResult(
            command_id=self.id,
            exit_code=0 if all_success else 1,
            stdout=stdout,
            stderr=stderr,
            error=None if all_success else "One or more push operations failed",
            duration=total_duration,
        )


class DockerBuildAndPushCommand(CustomCommand):
    """Build and push Docker image in sequence."""

    def __init__(self) -> None:
        super().__init__(
            command_id="docker-build_and_push",
            title="Build & Push",
            description="Build and push Docker image to registry",
            group_id="docker",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute build then push."""
        build_cmd = DockerBuildCommand()
        push_cmd = DockerPushCommand()

        # Build first
        build_result = await build_cmd.execute(ctx)
        if not build_result.success:
            return CommandResult(
                command_id=self.id,
                exit_code=build_result.exit_code,
                stdout=build_result.stdout,
                stderr=build_result.stderr,
                error=f"Build failed: {build_result.error or 'Unknown error'}",
                duration=build_result.duration,
            )

        # Push after successful build
        push_result = await push_cmd.execute(ctx)

        return CommandResult(
            command_id=self.id,
            exit_code=push_result.exit_code,
            stdout=f"{build_result.stdout}\n{push_result.stdout}".strip(),
            stderr=f"{build_result.stderr}\n{push_result.stderr}".strip(),
            error=push_result.error,
            duration=(build_result.duration or 0) + (push_result.duration or 0),
        )


class DockerGroup(CommandGroup):
    """Docker command group for container and image management."""

    def __init__(self) -> None:
        super().__init__(
            group_id="docker",
            title="Docker",
            description="Docker container and image commands",
            order=3,
        )
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        """Create all Docker commands."""
        project_name = "{project_name}"  # Template, expanded at runtime

        return [
            DockerBuildCommand(),
            DockerPushCommand(),
            DockerBuildAndPushCommand(),
            ShellCommand(
                id="docker-up",
                shell=f"docker run -d --name {project_name} {project_name}:latest || docker start {project_name}",
                title="Up",
                description="Start Docker container",
                group_id=self.id,
            ),
            ShellCommand(
                id="docker-down",
                shell=f"docker stop {project_name} || echo 'Container not running'",
                title="Down",
                description="Stop Docker container",
                group_id=self.id,
            ),
            ShellCommand(
                id="docker-restart",
                shell=f"docker restart $(docker ps -q --filter 'name={project_name}') || echo 'No container running'",
                title="Restart",
                description="Restart Docker container",
                group_id=self.id,
            ),
            ShellCommand(
                id="docker-logs",
                shell=f"docker logs -f {project_name}",
                title="Logs",
                description="Follow Docker container logs",
                group_id=self.id,
                watch=True,
            ),
            ShellCommand(
                id="docker-logs-tail",
                shell=f"docker logs --tail 100 {project_name}",
                title="Logs (Tail)",
                description="Show last 100 lines of Docker container logs",
                group_id=self.id,
            ),
        ]

    def get_commands(self):
        """Get all commands in this group."""
        return self._commands
