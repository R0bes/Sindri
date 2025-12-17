"""Extensible template engine for variable expansion."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from sindri.core.context import ExecutionContext


class TemplateEngine:
    """
    Extensible template expansion engine.
    
    Supports both {var} and ${var} syntax.
    Variables are resolved lazily via registered resolver functions.
    """

    def __init__(self) -> None:
        self._resolvers: dict[str, Callable[[ExecutionContext], str]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default template variables."""
        
        def resolve_project_name(ctx: ExecutionContext) -> str:
            if ctx.config and ctx.config.project_name:
                return ctx.config.project_name
            return ctx.cwd.name

        def resolve_registry(ctx: ExecutionContext) -> str:
            if ctx.config and ctx.config._defaults:
                return ctx.config._defaults.docker_registry or "localhost:5000"
            return "localhost:5000"

        def resolve_version(ctx: ExecutionContext) -> str:
            return _get_project_version(ctx.cwd)

        def resolve_cwd(ctx: ExecutionContext) -> str:
            return str(ctx.cwd)

        self.register("project_name", resolve_project_name)
        self.register("registry", resolve_registry)
        self.register("version", resolve_version)
        self.register("cwd", resolve_cwd)

    def register(
        self,
        name: str,
        resolver: Callable[[ExecutionContext], str],
    ) -> None:
        """
        Register a template variable resolver.
        
        Args:
            name: Variable name (without braces)
            resolver: Function that takes ExecutionContext and returns string value
        """
        self._resolvers[name] = resolver

    def unregister(self, name: str) -> bool:
        """
        Unregister a template variable.
        
        Returns True if variable was registered, False otherwise.
        """
        if name in self._resolvers:
            del self._resolvers[name]
            return True
        return False

    def expand(self, text: str, ctx: ExecutionContext) -> str:
        """
        Expand all template variables in text.
        
        Supports both {var} and ${var} syntax.
        Unknown variables are left unchanged.
        
        Args:
            text: Text containing template variables
            ctx: Execution context for variable resolution
            
        Returns:
            Text with variables expanded
        """
        result = text

        for name, resolver in self._resolvers.items():
            # Match both {var} and ${var} patterns
            patterns = [f"{{{name}}}", f"${{{name}}}"]
            
            # Only resolve if pattern is found (lazy evaluation)
            value: str | None = None
            for pattern in patterns:
                if pattern in result:
                    if value is None:
                        try:
                            value = resolver(ctx)
                        except Exception:
                            # If resolver fails, leave variable unchanged
                            continue
                    result = result.replace(pattern, value)

        return result

    def get_variables(self) -> list[str]:
        """Get list of registered variable names."""
        return list(self._resolvers.keys())

    def has_variable(self, name: str) -> bool:
        """Check if a variable is registered."""
        return name in self._resolvers


def _get_project_version(cwd: Path) -> str:
    """Get project version from pyproject.toml."""
    pyproject = cwd / "pyproject.toml"
    if not pyproject.exists():
        return "latest"

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return "latest"

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        
        # Try [project] section first (PEP 621)
        if "project" in data and "version" in data["project"]:
            return data["project"]["version"]
        
        # Try [tool.poetry] section
        if "tool" in data and "poetry" in data["tool"]:
            if "version" in data["tool"]["poetry"]:
                return data["tool"]["poetry"]["version"]
        
        return "latest"
    except Exception:
        return "latest"


# Global default template engine instance
_default_engine: TemplateEngine | None = None


def get_template_engine() -> TemplateEngine:
    """Get the global template engine instance."""
    global _default_engine
    if _default_engine is None:
        _default_engine = TemplateEngine()
    return _default_engine
