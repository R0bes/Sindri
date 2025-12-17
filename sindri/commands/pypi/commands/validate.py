"""PyPI validate command."""

import asyncio
from pathlib import Path
from typing import Any, Dict

from sindri.commands.command import Command
from sindri.runner import AsyncExecutionEngine, CommandResult


class PyPIValidateCommand(Command):
    """Validate package for PyPI publishing."""

    def __init__(self):
        super().__init__(
            command_id="pypi-validate",
            title="Validate",
            description="Validate package build and metadata",
        )

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """Execute validation."""
        results = []
        
        # Check if build tools are installed
        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "pip", "show", "build", "twine",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            if process.returncode != 0:
                results.append("⚠ Installing build and twine...")
                install_process = await asyncio.create_subprocess_exec(
                    "python", "-m", "pip", "install", "build", "twine",
                    cwd=str(cwd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await install_process.communicate()
                if install_process.returncode != 0:
                    return CommandResult(
                        command_id=self.command_id,
                        exit_code=1,
                        error="Failed to install build tools",
                    )
                results.append("✓ Build tools installed")
        except Exception as e:
            return CommandResult(
                command_id=self.command_id,
                exit_code=1,
                error=f"Error checking build tools: {e}",
            )

        # Check pyproject.toml exists
        pyproject_path = cwd / "pyproject.toml"
        if not pyproject_path.exists():
            return CommandResult(
                command_id=self.command_id,
                exit_code=1,
                error="pyproject.toml not found",
            )
        results.append("✓ pyproject.toml found")

        # Validate with check
        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "build", "--check",
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return CommandResult(
                    command_id=self.command_id,
                    exit_code=process.returncode,
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    error="Package validation failed",
                )
            
            results.append("✓ Package validation passed")
            
            return CommandResult(
                command_id=self.command_id,
                exit_code=0,
                stdout="\n".join(results) + "\n" + stdout.decode(),
            )
        except Exception as e:
            return CommandResult(
                command_id=self.command_id,
                exit_code=1,
                error=f"Error validating package: {e}",
            )

