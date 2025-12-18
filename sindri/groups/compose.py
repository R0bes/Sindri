"""Docker Compose command group - service orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from sindri.core.command import CustomCommand
from sindri.core.group import CommandGroup
from sindri.core.result import CommandResult

if TYPE_CHECKING:
    from sindri.core.context import ExecutionContext


class ComposeGroup(CommandGroup):
    """Docker Compose command group for service orchestration."""

    def __init__(self, compose_file: Optional[str] = None) -> None:
        """
        Initialize Docker Compose command group.

        Args:
            compose_file: Path to compose file (defaults to auto-detect)
        """
        super().__init__(
            group_id="compose",
            title="Docker Compose",
            description="Docker Compose service commands",
            order=4,
        )
        self.compose_file = compose_file
        self._commands = self._create_commands()

    def _find_compose_file(self, cwd: Path) -> str:
        """Find docker-compose file in project directory."""
        if self.compose_file:
            return self.compose_file

        # Try common compose file names in order of preference
        compose_files = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ]

        for compose_file in compose_files:
            if (cwd / compose_file).exists():
                return compose_file

        # Default to docker-compose.yml if none found
        return "docker-compose.yml"

    def _compose_cmd(self, action: str, flags: Optional[str] = None, cwd: Optional[Path] = None) -> str:
        """Build Docker Compose command string."""
        if cwd:
            compose_file = self._find_compose_file(cwd)
        else:
            compose_file = self.compose_file or "docker-compose.yml"

        cmd = f"docker compose -f {compose_file} {action}"
        if flags:
            cmd += f" {flags}"
        return cmd

    def _create_commands(self) -> list:
        """Create all Compose commands."""
        return [
            ComposeUpCommand(),
            ComposeDownCommand(),
            ComposeRestartCommand(),
            ComposeBuildCommand(),
            ComposeLogsCommand(),
            ComposeLogsTailCommand(),
            ComposePsCommand(),
            ComposePullCommand(),
        ]

    def get_commands(self):
        """Get all commands in this group."""
        return self._commands


class ComposeUpCommand(CustomCommand):
    """Start Docker Compose services."""

    def __init__(self) -> None:
        super().__init__(
            command_id="compose-up",
            title="Up",
            description="Start Docker Compose services (detached mode)",
            group_id="compose",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute compose up."""
        from sindri.core.shell_runner import run_shell_command

        compose_group = ComposeGroup()
        shell = compose_group._compose_cmd("up", "-d", ctx.cwd)

        return await run_shell_command(
            command_id=self.id,
            shell=shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )


class ComposeDownCommand(CustomCommand):
    """Stop Docker Compose services."""

    def __init__(self) -> None:
        super().__init__(
            command_id="compose-down",
            title="Down",
            description="Stop Docker Compose services",
            group_id="compose",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute compose down."""
        from sindri.core.shell_runner import run_shell_command

        compose_group = ComposeGroup()
        shell = compose_group._compose_cmd("down", None, ctx.cwd)

        return await run_shell_command(
            command_id=self.id,
            shell=shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )


class ComposeRestartCommand(CustomCommand):
    """Restart Docker Compose services."""

    def __init__(self) -> None:
        super().__init__(
            command_id="compose-restart",
            title="Restart",
            description="Restart Docker Compose services",
            group_id="compose",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute compose restart."""
        from sindri.core.shell_runner import run_shell_command

        compose_group = ComposeGroup()
        shell = compose_group._compose_cmd("restart", None, ctx.cwd)

        return await run_shell_command(
            command_id=self.id,
            shell=shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )


class ComposeBuildCommand(CustomCommand):
    """Build Docker Compose images."""

    def __init__(self) -> None:
        super().__init__(
            command_id="compose-build",
            title="Build",
            description="Build Docker Compose images",
            group_id="compose",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute compose build."""
        from sindri.core.shell_runner import run_shell_command

        compose_group = ComposeGroup()
        shell = compose_group._compose_cmd("build", None, ctx.cwd)

        return await run_shell_command(
            command_id=self.id,
            shell=shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )


class ComposeLogsCommand(CustomCommand):
    """Follow Docker Compose logs."""

    def __init__(self) -> None:
        super().__init__(
            command_id="compose-logs",
            title="Logs",
            description="Follow Docker Compose logs",
            group_id="compose",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute compose logs -f."""
        from sindri.core.shell_runner import run_shell_command

        compose_group = ComposeGroup()
        shell = compose_group._compose_cmd("logs", "-f", ctx.cwd)

        return await run_shell_command(
            command_id=self.id,
            shell=shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )


class ComposeLogsTailCommand(CustomCommand):
    """Show last 100 lines of Docker Compose logs."""

    def __init__(self) -> None:
        super().__init__(
            command_id="compose-logs-tail",
            title="Logs (Tail)",
            description="Show last 100 lines of Docker Compose logs",
            group_id="compose",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute compose logs --tail=100."""
        from sindri.core.shell_runner import run_shell_command

        compose_group = ComposeGroup()
        shell = compose_group._compose_cmd("logs", "--tail=100", ctx.cwd)

        return await run_shell_command(
            command_id=self.id,
            shell=shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )


class ComposePsCommand(CustomCommand):
    """Show Docker Compose service status."""

    def __init__(self) -> None:
        super().__init__(
            command_id="compose-ps",
            title="Status",
            description="Show Docker Compose service status",
            group_id="compose",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute compose ps."""
        from sindri.core.shell_runner import run_shell_command

        compose_group = ComposeGroup()
        shell = compose_group._compose_cmd("ps", None, ctx.cwd)

        return await run_shell_command(
            command_id=self.id,
            shell=shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )


class ComposePullCommand(CustomCommand):
    """Pull Docker Compose images."""

    def __init__(self) -> None:
        super().__init__(
            command_id="compose-pull",
            title="Pull",
            description="Pull Docker Compose images",
            group_id="compose",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute compose pull."""
        from sindri.core.shell_runner import run_shell_command

        compose_group = ComposeGroup()
        shell = compose_group._compose_cmd("pull", None, ctx.cwd)

        return await run_shell_command(
            command_id=self.id,
            shell=shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )
