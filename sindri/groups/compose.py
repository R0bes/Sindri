"""Docker Compose command group - service orchestration."""

from __future__ import annotations

from typing import Optional

from sindri.core.command import ShellCommand
from sindri.core.group import CommandGroup


class ComposeGroup(CommandGroup):
    """Docker Compose command group for service orchestration."""

    def __init__(self, compose_file: Optional[str] = None) -> None:
        """
        Initialize Docker Compose command group.

        Args:
            compose_file: Path to compose file (defaults to docker-compose.yml)
        """
        super().__init__(
            group_id="compose",
            title="Docker Compose",
            description="Docker Compose service commands",
            order=4,
        )
        self.compose_file = compose_file or "docker-compose.yml"
        self._commands = self._create_commands()

    def _compose_cmd(self, action: str, flags: Optional[str] = None) -> str:
        """Build Docker Compose command string."""
        cmd = f"docker compose -f {self.compose_file} {action}"
        if flags:
            cmd += f" {flags}"
        return cmd

    def _create_commands(self) -> list:
        """Create all Compose commands."""
        return [
            ShellCommand(
                id="compose-up",
                shell=self._compose_cmd("up", "-d"),
                title="Up",
                description="Start Docker Compose services (detached)",
                group_id=self.id,
            ),
            ShellCommand(
                id="compose-down",
                shell=self._compose_cmd("down"),
                title="Down",
                description="Stop Docker Compose services",
                group_id=self.id,
            ),
            ShellCommand(
                id="compose-restart",
                shell=self._compose_cmd("restart"),
                title="Restart",
                description="Restart Docker Compose services",
                group_id=self.id,
            ),
            ShellCommand(
                id="compose-build",
                shell=self._compose_cmd("build"),
                title="Build",
                description="Build Docker Compose images",
                group_id=self.id,
            ),
            ShellCommand(
                id="compose-logs",
                shell=self._compose_cmd("logs", "-f"),
                title="Logs",
                description="Follow Docker Compose logs",
                group_id=self.id,
                watch=True,
            ),
            ShellCommand(
                id="compose-logs-tail",
                shell=self._compose_cmd("logs", "--tail=100"),
                title="Logs (Tail)",
                description="Show last 100 lines of Docker Compose logs",
                group_id=self.id,
            ),
            ShellCommand(
                id="compose-ps",
                shell=self._compose_cmd("ps"),
                title="Status",
                description="Show Docker Compose service status",
                group_id=self.id,
            ),
            ShellCommand(
                id="compose-pull",
                shell=self._compose_cmd("pull"),
                title="Pull",
                description="Pull Docker Compose images",
                group_id=self.id,
            ),
        ]

    def get_commands(self):
        """Get all commands in this group."""
        return self._commands
