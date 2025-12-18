"""PyPI command group - package publishing."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from sindri.core.command import CustomCommand
from sindri.core.group import CommandGroup
from sindri.core.result import CommandResult

if TYPE_CHECKING:
    from sindri.core.context import ExecutionContext


def _find_project_root(cwd: Path) -> Optional[Path]:
    """Find project root with pyproject.toml."""
    current = cwd
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return None


class PyPIValidateCommand(CustomCommand):
    """Validate package for PyPI publishing."""

    def __init__(self) -> None:
        super().__init__(
            command_id="pypi-validate",
            title="Validate",
            description="Validate package build and metadata",
            group_id="pypi",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute validation."""
        results = []

        # Check build tools
        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "pip", "show", "build", "twine",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()

            if process.returncode != 0:
                results.append("⚠ Installing build and twine...")
                install = await asyncio.create_subprocess_exec(
                    "python", "-m", "pip", "install", "build", "twine",
                    cwd=str(ctx.cwd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await install.communicate()
                if install.returncode != 0:
                    return CommandResult(
                        command_id=self.id,
                        exit_code=1,
                        error="Failed to install build tools",
                    )
                results.append("✓ Build tools installed")
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Error checking build tools: {e}",
            )

        # Check pyproject.toml
        project_root = _find_project_root(ctx.cwd)
        if not project_root:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error="pyproject.toml not found",
            )
        results.append("✓ pyproject.toml found")

        # Build package to validate it can be built
        try:
            results.append("📦 Building package to validate...")
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "build",
                cwd=str(project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return CommandResult(
                    command_id=self.id,
                    exit_code=process.returncode,
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    error="Package build validation failed",
                )

            results.append("✓ Package build validation passed")
            
            # Validate built distributions with twine check
            dist_path = project_root / "dist"
            if dist_path.exists():
                dist_files = list(dist_path.glob("*"))
                if dist_files:
                    check_process = await asyncio.create_subprocess_exec(
                        "python", "-m", "twine", "check", *[str(f) for f in dist_files],
                        cwd=str(project_root),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    check_stdout, check_stderr = await check_process.communicate()
                    
                    if check_process.returncode != 0:
                        return CommandResult(
                            command_id=self.id,
                            exit_code=check_process.returncode,
                            stdout=stdout.decode() + "\n" + check_stdout.decode(),
                            stderr=stderr.decode() + "\n" + check_stderr.decode(),
                            error="Package metadata validation failed",
                        )
                    results.append("✓ Package metadata validation passed")

            return CommandResult(
                command_id=self.id,
                exit_code=0,
                stdout="\n".join(results) + "\n" + stdout.decode(),
            )
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Error validating package: {e}",
            )


class PyPIPushCommand(CustomCommand):
    """Build and upload package to PyPI."""

    def __init__(self) -> None:
        super().__init__(
            command_id="pypi-push",
            title="Push",
            description="Build and upload package to PyPI",
            group_id="pypi",
        )

    async def execute(
        self,
        ctx: ExecutionContext,
        repository: Optional[str] = None,
        test: bool = False,
        **kwargs: Any,
    ) -> CommandResult:
        """Execute build and upload."""
        results = []

        # Find project root
        project_root = _find_project_root(ctx.cwd)
        if not project_root:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error="pyproject.toml not found",
            )

        # Check build tools
        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "pip", "show", "build", "twine",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()

            if process.returncode != 0:
                results.append("⚠ Installing build and twine...")
                install = await asyncio.create_subprocess_exec(
                    "python", "-m", "pip", "install", "build", "twine",
                    cwd=str(project_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await install.communicate()
                if install.returncode != 0:
                    return CommandResult(
                        command_id=self.id,
                        exit_code=1,
                        error="Failed to install build tools",
                    )
                results.append("✓ Build tools installed")
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Error checking build tools: {e}",
            )

        # Clean dist directory
        dist_path = project_root / "dist"
        if dist_path.exists():
            shutil.rmtree(dist_path)
            results.append("✓ Cleaned dist directory")

        # Build package
        try:
            results.append("📦 Building package...")
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "build",
                cwd=str(project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return CommandResult(
                    command_id=self.id,
                    exit_code=process.returncode,
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    error="Package build failed",
                )

            results.append("✓ Package built successfully")
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Error building package: {e}",
            )

        # Upload to PyPI
        try:
            target = "Test PyPI" if test else "PyPI"
            results.append(f"📤 Uploading to {target}...")

            upload_cmd = ["python", "-m", "twine", "upload"]
            if test:
                upload_cmd.extend(["--repository", "testpypi"])
            elif repository:
                upload_cmd.extend(["--repository", repository])

            upload_cmd.append("dist/*")

            process = await asyncio.create_subprocess_exec(
                *upload_cmd,
                cwd=str(project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return CommandResult(
                    command_id=self.id,
                    exit_code=process.returncode,
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    error=f"Upload to {target} failed",
                )

            results.append(f"✓ Uploaded to {target}")

            return CommandResult(
                command_id=self.id,
                exit_code=0,
                stdout="\n".join(results) + "\n" + stdout.decode(),
            )
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Error uploading package: {e}",
            )


class PyPIGroup(CommandGroup):
    """PyPI command group for package publishing."""

    def __init__(self) -> None:
        super().__init__(
            group_id="pypi",
            title="PyPI",
            description="PyPI package publishing commands",
            order=6,
        )
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        """Create all PyPI commands."""
        return [
            PyPIValidateCommand(),
            PyPIPushCommand(),
        ]

    def get_commands(self):
        """Get all commands in this group."""
        return self._commands
