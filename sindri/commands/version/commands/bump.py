"""Version bump command."""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from sindri.commands.command import Command
from sindri.runner import AsyncExecutionEngine, CommandResult
from sindri.utils.helper import get_project_version_from_pyproject


class VersionBumpCommand(Command):
    """Bump version command."""

    def __init__(self):
        super().__init__(
            command_id="version bump",
            title="Bump",
            description="Bump version number",
        )

    def _parse_version(self, version: str) -> tuple[int, int, int]:
        """Parse version string into major, minor, patch."""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    def _bump_version(
        self, version: str, bump_type: Optional[str] = None
    ) -> str:
        """
        Bump version based on type.

        Args:
            version: Current version string
            bump_type: 'major', 'minor', 'patch', or None for auto-detect

        Returns:
            New version string
        """
        major, minor, patch = self._parse_version(version)

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            # Default to patch if no type specified
            return f"{major}.{minor}.{patch + 1}"

    def _update_pyproject_version(
        self, pyproject_path: Path, new_version: str
    ) -> None:
        """Update version in pyproject.toml file."""
        content = pyproject_path.read_text(encoding="utf-8")
        # Replace version line - handle both quoted and unquoted versions
        # Pattern matches: version = "0.1.0" or version = 0.1.0
        # Match: version = "0.1.0" or version = 0.1.0
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.strip().startswith("version"):
                # Match version line
                match = re.match(r'(version\s*=\s*)(["\']?)([^"\'\n]+)(["\']?)', line)
                if match:
                    prefix = match.group(1)
                    quote1 = match.group(2)
                    quote2 = match.group(4)
                    new_line = f"{prefix}{quote1}{new_version}{quote2}"
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        new_content = "\n".join(new_lines)
        pyproject_path.write_text(new_content, encoding="utf-8")

    async def execute(
        self,
        engine: AsyncExecutionEngine,
        cwd: Path,
        env: Dict[str, str],
        **kwargs: Any,
    ) -> CommandResult:
        """
        Execute version bump command.

        Args:
            engine: Execution engine instance
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional arguments (bump_type: 'major', 'minor', 'patch')

        Returns:
            CommandResult with new version
        """
        # Get current version
        current_version = get_project_version_from_pyproject(cwd)
        if not current_version:
            return CommandResult(
                self.command_id,
                1,
                error="Could not determine current version from pyproject.toml",
            )

        # Get bump type from kwargs
        bump_type = kwargs.get("bump_type")

        # Bump version
        try:
            new_version = self._bump_version(current_version, bump_type)
        except ValueError as e:
            return CommandResult(
                self.command_id,
                1,
                error=str(e),
            )

        # Find and update pyproject.toml
        pyproject_path = None
        current = cwd
        while current != current.parent:
            potential_path = current / "pyproject.toml"
            if potential_path.exists():
                pyproject_path = potential_path
                break
            current = current.parent

        if not pyproject_path:
            return CommandResult(
                self.command_id,
                1,
                error="pyproject.toml not found",
            )

        # Update version in pyproject.toml
        try:
            self._update_pyproject_version(pyproject_path, new_version)
        except Exception as e:
            return CommandResult(
                self.command_id,
                1,
                error=f"Failed to update pyproject.toml: {e}",
            )

        return CommandResult(
            self.command_id,
            0,
            stdout=f"Version bumped from {current_version} to {new_version}",
        )

