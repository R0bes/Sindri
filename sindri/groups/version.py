"""Version command group - version management."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from sindri.core.command import CustomCommand
from sindri.core.group import CommandGroup
from sindri.core.result import CommandResult

if TYPE_CHECKING:
    from sindri.core.context import ExecutionContext


def _get_version_from_pyproject(cwd: Path) -> Optional[str]:
    """Get version from pyproject.toml."""
    pyproject = cwd / "pyproject.toml"
    if not pyproject.exists():
        # Search upwards
        current = cwd
        while current != current.parent:
            potential = current / "pyproject.toml"
            if potential.exists():
                pyproject = potential
                break
            current = current.parent
        else:
            return None

    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore

        with open(pyproject, "rb") as f:
            data = tomllib.load(f)

        if "project" in data and "version" in data["project"]:
            return data["project"]["version"]
        if "tool" in data and "poetry" in data["tool"]:
            return data["tool"]["poetry"].get("version")
        return None
    except Exception:
        return None


def _get_project_name_from_pyproject(cwd: Path) -> Optional[str]:
    """Get project name from pyproject.toml."""
    pyproject = cwd / "pyproject.toml"
    if not pyproject.exists():
        current = cwd
        while current != current.parent:
            potential = current / "pyproject.toml"
            if potential.exists():
                pyproject = potential
                break
            current = current.parent
        else:
            return None

    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore

        with open(pyproject, "rb") as f:
            data = tomllib.load(f)

        if "project" in data and "name" in data["project"]:
            return data["project"]["name"]
        if "tool" in data and "poetry" in data["tool"]:
            return data["tool"]["poetry"].get("name")
        return None
    except Exception:
        return None


class VersionShowCommand(CustomCommand):
    """Show current version information."""

    def __init__(self) -> None:
        super().__init__(
            command_id="version show",
            title="Show",
            description="Show current version",
            group_id="version",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute version show."""
        project_name = _get_project_name_from_pyproject(ctx.cwd)
        version = _get_version_from_pyproject(ctx.cwd)

        if project_name and version:
            output = f"{project_name} {version}"
        elif version:
            output = version
        else:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error="Version information not available (no pyproject.toml found)",
            )

        return CommandResult(
            command_id=self.id,
            exit_code=0,
            stdout=output,
        )


class VersionBumpCommand(CustomCommand):
    """Bump version number."""

    def __init__(self) -> None:
        super().__init__(
            command_id="version bump",
            title="Bump",
            description="Bump version number (--major, --minor, --patch)",
            group_id="version",
        )

    def _parse_version(self, version: str) -> tuple[int, int, int]:
        """Parse semver string into components."""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    def _bump_version(self, version: str, bump_type: Optional[str] = None) -> str:
        """Bump version based on type."""
        major, minor, patch = self._parse_version(version)

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # Default to patch
            return f"{major}.{minor}.{patch + 1}"

    def _find_pyproject(self, cwd: Path) -> Optional[Path]:
        """Find pyproject.toml file."""
        current = cwd
        while current != current.parent:
            potential = current / "pyproject.toml"
            if potential.exists():
                return potential
            current = current.parent
        return None

    def _update_pyproject_version(self, pyproject_path: Path, new_version: str) -> None:
        """Update version in pyproject.toml."""
        content = pyproject_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        new_lines = []

        for line in lines:
            if line.strip().startswith("version"):
                match = re.match(r'(version\s*=\s*)(["\']?)([^"\'\n]+)(["\']?)', line)
                if match:
                    prefix = match.group(1)
                    quote1 = match.group(2)
                    quote2 = match.group(4)
                    new_lines.append(f"{prefix}{quote1}{new_version}{quote2}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        pyproject_path.write_text("\n".join(new_lines), encoding="utf-8")

    async def execute(self, ctx: ExecutionContext, **kwargs: Any) -> CommandResult:
        """Execute version bump."""
        current_version = _get_version_from_pyproject(ctx.cwd)
        if not current_version:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error="Could not determine current version from pyproject.toml",
            )

        bump_type = kwargs.get("bump_type")

        try:
            new_version = self._bump_version(current_version, bump_type)
        except ValueError as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=str(e),
            )

        pyproject_path = self._find_pyproject(ctx.cwd)
        if not pyproject_path:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error="pyproject.toml not found",
            )

        try:
            self._update_pyproject_version(pyproject_path, new_version)
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Failed to update pyproject.toml: {e}",
            )

        return CommandResult(
            command_id=self.id,
            exit_code=0,
            stdout=f"Version bumped: {current_version} → {new_version}",
        )


class VersionTagCommand(CustomCommand):
    """Create git tag for current version."""

    def __init__(self) -> None:
        super().__init__(
            command_id="version tag",
            title="Tag",
            description="Create git tag for current version",
            group_id="version",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute version tag."""
        from sindri.core.shell_runner import run_shell_command

        version = _get_version_from_pyproject(ctx.cwd)
        if not version:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error="Could not determine current version from pyproject.toml",
            )

        tag_name = f"v{version}"
        tag_shell = f'git tag -a "{tag_name}" -m "Version {version}"'

        result = await run_shell_command(
            command_id=self.id,
            shell=tag_shell,
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )

        if result.success:
            return CommandResult(
                command_id=self.id,
                exit_code=0,
                stdout=f"Created tag: {tag_name}",
            )
        else:
            return CommandResult(
                command_id=self.id,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                error=result.error or "Failed to create git tag",
            )


class VersionGroup(CommandGroup):
    """Version command group for version management."""

    def __init__(self) -> None:
        super().__init__(
            group_id="version",
            title="Version",
            description="Version management commands",
            order=2,
        )
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        """Create all version commands."""
        return [
            VersionShowCommand(),
            VersionBumpCommand(),
            VersionTagCommand(),
        ]

    def get_commands(self):
        """Get all commands in this group."""
        return self._commands
