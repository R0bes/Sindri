"""Docker Compose command group."""

from typing import Optional

from sindri.commands.command import Command
from sindri.commands.group import CommandGroup
from sindri.commands.shell_command import ShellCommand


class ComposeGroup(CommandGroup):
    """
    Docker Compose command group with shared logic for Compose operations.

    Provides common functionality for Docker Compose commands.
    """

    def __init__(self, compose_file: Optional[str] = None):
        """
        Initialize Docker Compose command group.

        Args:
            compose_file: Path to docker-compose.yml file
                (defaults to docker-compose.yml)
        """
        super().__init__(
            group_id="compose",
            title="Docker Compose",
            description="Docker Compose service commands",
            order=4,
        )
        self.compose_file = compose_file or "docker-compose.yml"
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _get_compose_cmd(self, action: str, flags: Optional[str] = None) -> str:
        """
        Build Docker Compose command.

        Args:
            action: Compose action (up, down, restart, build, etc.)
            flags: Additional flags (e.g., "-d", "--build")

        Returns:
            Full docker compose command
        """
        cmd = f"docker compose -f {self.compose_file} {action}"
        if flags:
            cmd += f" {flags}"
        return cmd

    def _initialize_commands(self) -> None:
        """Initialize Docker Compose commands."""
        self._command_list = [
            ShellCommand(
                command_id="compose-restart",
                shell=self._get_compose_cmd("restart"),
                title="Rebuild+Restart",
                description="Restart Docker Compose services",
            ),
            ShellCommand(
                command_id="compose-re",
                shell=self._get_compose_cmd("restart"),
                title="Rebuild+Restart",
                description="Restart Docker Compose services (alias)",
            ),
            ShellCommand(
                command_id="compose-up",
                shell=self._get_compose_cmd("up", "-d"),
                title="Up",
                description="Start Docker Compose services",
            ),
            ShellCommand(
                command_id="compose-down",
                shell=self._get_compose_cmd("down"),
                title="Down",
                description="Stop Docker Compose services",
            ),
            ShellCommand(
                command_id="compose-build",
                shell=self._get_compose_cmd("build"),
                title="Build",
                description="Build Docker Compose images",
            ),
        ]

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list

