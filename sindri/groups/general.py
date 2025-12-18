"""General command group - setup, install, etc."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from sindri.core.command import CustomCommand
from sindri.core.group import CommandGroup
from sindri.core.result import CommandResult
from sindri.utils.venv_helper import get_venv_path, get_venv_python

if TYPE_CHECKING:
    from sindri.core.context import ExecutionContext


class SetupVenvCommand(CustomCommand):
    """Create virtual environment in .venv."""

    def __init__(self) -> None:
        super().__init__(
            command_id="setup-venv",
            title="Venv",
            description="Create virtual environment in .venv",
            group_id="general",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Create virtual environment and output activation instructions."""
        from sindri.core.shell_runner import run_shell_command

        venv_path = get_venv_path(ctx.cwd)

        # Check if venv already exists
        if venv_path.exists():
            python_path = get_venv_python(ctx.cwd)
            if python_path and Path(python_path).exists():
                activation_cmd = (
                    ".venv\\Scripts\\activate"
                    if os.name == "nt"
                    else "source .venv/bin/activate"
                )
                return CommandResult(
                    command_id=self.id,
                    exit_code=0,
                    stdout=(
                        f"Virtual environment already exists at {venv_path}\n"
                        f"To activate, run: {activation_cmd}"
                    ),
                )

        # Create venv
        if os.name == "nt":  # Windows
            create_cmd = "python -m venv .venv"
        else:  # Unix
            create_cmd = "python -m venv .venv"

        result = await run_shell_command(
            command_id=self.id,
            shell=create_cmd,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )

        if not result.success:
            return CommandResult(
                command_id=self.id,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                error=f"Failed to create virtual environment: {result.error}",
            )

        # Output activation instructions
        activation_cmd = (
            ".venv\\Scripts\\activate"
            if os.name == "nt"
            else "source .venv/bin/activate"
        )
        activation_msg = (
            f"Virtual environment created at {venv_path}\n"
            f"To activate, run: {activation_cmd}"
        )

        return CommandResult(
            command_id=self.id,
            exit_code=0,
            stdout=f"{result.stdout}\n{activation_msg}".strip(),
        )


class SetupInstallCommand(CustomCommand):
    """Install project with dev dependencies in .venv."""

    def __init__(self) -> None:
        super().__init__(
            command_id="setup-install",
            title="Install",
            description="Install project in development mode with dev dependencies",
            group_id="general",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Install project with dev dependencies."""
        from sindri.core.shell_runner import run_shell_command

        venv_path = get_venv_path(ctx.cwd)
        python_path = get_venv_python(ctx.cwd)

        # Check if venv exists, create if not
        if not python_path or not Path(python_path).exists():
            # Create venv first
            if os.name == "nt":  # Windows
                create_cmd = "python -m venv .venv"
            else:  # Unix
                create_cmd = "python -m venv .venv"

            create_result = await run_shell_command(
                command_id=f"{self.id}-create-venv",
                shell=create_cmd,
                cwd=ctx.cwd,
                env=ctx.get_env(),
                stream_callback=ctx.stream_callback,
            )

            if not create_result.success:
                # Fallback to system Python with --break-system-packages
                install_cmd = "pip install -e '.[dev]' --break-system-packages"
                return await run_shell_command(
                    command_id=self.id,
                    shell=install_cmd,
                    cwd=ctx.cwd,
                    env=ctx.get_env(),
                    stream_callback=ctx.stream_callback,
                )

            # Refresh python_path after venv creation
            python_path = get_venv_python(ctx.cwd)

        # Install with dev dependencies using venv Python
        if python_path and Path(python_path).exists():
            install_cmd = f"{python_path} -m pip install -e '.[dev]'"
        else:
            # Fallback to system Python
            install_cmd = "pip install -e '.[dev]' --break-system-packages"

        result = await run_shell_command(
            command_id=self.id,
            shell=install_cmd,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )

        return result


class GeneralGroup(CommandGroup):
    """General project commands like setup and install."""

    def __init__(self) -> None:
        super().__init__(
            group_id="general",
            title="General",
            description="General project setup and installation commands",
            order=1,
        )
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        return [
            SetupVenvCommand(),
            SetupInstallCommand(),
        ]

    def get_commands(self):
        return self._commands
