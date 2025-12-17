"""PyPI push command."""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from sindri.commands.command import Command
from sindri.runner import AsyncExecutionEngine, CommandResult
from sindri.utils import find_project_root


class PyPIPushCommand(Command):
    """Build and upload package to PyPI."""

    def __init__(self):
        super().__init__(
            command_id="pypi-push",
            title="Push",
            description="Build and upload package to PyPI",
        )

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        repository: Optional[str] = None,
        test: bool = False,
        **kwargs: Any,
    ) -> CommandResult:
        """Execute build and upload."""
        results = []
        
        # Find project root - try multiple strategies
        # 1. engine.config_dir (should be project root from get_config_dir)
        # 2. cwd if it has pyproject.toml
        # 3. search upwards from cwd
        project_root = None
        if engine.config_dir and (engine.config_dir / "pyproject.toml").exists():
            project_root = engine.config_dir
        elif (cwd / "pyproject.toml").exists():
            project_root = cwd
        else:
            found_root = find_project_root(cwd)
            if found_root and (found_root / "pyproject.toml").exists():
                project_root = found_root
        
        if project_root is None:
            return CommandResult(
                command_id=self.command_id,
                exit_code=1,
                error=(
                    f"pyproject.toml not found. "
                    f"engine.config_dir={engine.config_dir}, cwd={cwd}"
                ),
            )
        
        pyproject_path = project_root / "pyproject.toml"
        
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
                    cwd=str(project_root),
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

        # Clean dist directory
        dist_path = project_root / "dist"
        if dist_path.exists():
            import shutil
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
                    command_id=self.command_id,
                    exit_code=process.returncode,
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    error="Package build failed",
                )
            
            results.append("✓ Package built successfully")
        except Exception as e:
            return CommandResult(
                command_id=self.command_id,
                exit_code=1,
                error=f"Error building package: {e}",
            )

        # Upload to PyPI
        try:
            results.append(f"📤 Uploading to {'Test PyPI' if test else 'PyPI'}...")
            
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
                    command_id=self.command_id,
                    exit_code=process.returncode,
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    error=f"Upload to {'Test PyPI' if test else 'PyPI'} failed",
                )
            
            results.append(f"✓ Uploaded to {'Test PyPI' if test else 'PyPI'}")
            
            return CommandResult(
                command_id=self.command_id,
                exit_code=0,
                stdout="\n".join(results) + "\n" + stdout.decode(),
            )
        except Exception as e:
            return CommandResult(
                command_id=self.command_id,
                exit_code=1,
                error=f"Error uploading package: {e}",
            )
