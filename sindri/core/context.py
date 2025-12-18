"""Execution context for commands."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from sindri.config.models import SindriConfig
    from sindri.core.templates import TemplateEngine


@dataclass
class ExecutionContext:
    """
    Execution context passed to all commands.
    
    Bundles all runtime parameters needed for command execution:
    - Working directory
    - Configuration
    - Environment variables
    - Execution options (dry_run, verbose, etc.)
    """

    cwd: Path
    config: Optional[SindriConfig] = None
    env: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False
    verbose: bool = False
    timeout: Optional[int] = None
    retries: int = 0
    
    # Callbacks
    stream_callback: Optional[Callable[[str, str], None]] = None
    
    # Internal
    _template_engine: Optional[TemplateEngine] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Ensure cwd is a Path object."""
        if isinstance(self.cwd, str):
            self.cwd = Path(self.cwd)
        self.cwd = self.cwd.resolve()

    @property
    def template_engine(self) -> TemplateEngine:
        """Get template engine, creating default if needed."""
        if self._template_engine is None:
            from sindri.core.templates import get_template_engine
            self._template_engine = get_template_engine()
        return self._template_engine

    @template_engine.setter
    def template_engine(self, engine: TemplateEngine) -> None:
        """Set custom template engine."""
        self._template_engine = engine

    def expand_templates(self, text: str) -> str:
        """
        Expand template variables in text.
        
        Convenience method that uses the context's template engine.
        """
        return self.template_engine.expand(text, self)

    def get_env(self, profile: Optional[str] = None) -> dict[str, str]:
        """
        Get merged environment variables.
        
        Merges in order (later overrides earlier):
        1. System environment (os.environ)
        2. Profile-specific env vars (if profile specified)
        3. Context-level env vars (highest priority)
        
        Args:
            profile: Optional environment profile (dev, test, prod)
            
        Returns:
            Merged environment dictionary
        """
        result = dict(os.environ)
        
        if profile and self.config:
            profile_env = self.config.get_env_vars(profile)
            result.update(profile_env)
        
        # Context env overrides everything
        result.update(self.env)
        
        return result

    def with_cwd(self, cwd: Path | str) -> ExecutionContext:
        """Create a new context with different working directory."""
        new_cwd = Path(cwd) if isinstance(cwd, str) else cwd
        if not new_cwd.is_absolute():
            new_cwd = (self.cwd / new_cwd).resolve()
        
        return ExecutionContext(
            cwd=new_cwd,
            config=self.config,
            env=self.env.copy(),
            dry_run=self.dry_run,
            verbose=self.verbose,
            timeout=self.timeout,
            retries=self.retries,
            stream_callback=self.stream_callback,
            _template_engine=self._template_engine,
        )

    def with_env(self, **env_vars: str) -> ExecutionContext:
        """Create a new context with additional environment variables."""
        new_env = self.env.copy()
        new_env.update(env_vars)
        
        return ExecutionContext(
            cwd=self.cwd,
            config=self.config,
            env=new_env,
            dry_run=self.dry_run,
            verbose=self.verbose,
            timeout=self.timeout,
            retries=self.retries,
            stream_callback=self.stream_callback,
            _template_engine=self._template_engine,
        )

    def resolve_path(self, path: str | Path) -> Path:
        """
        Resolve a path relative to the context's working directory.
        
        Absolute paths are returned unchanged (even on Windows).
        Relative paths are resolved against cwd.
        """
        p = Path(path) if isinstance(path, str) else path
        # On Windows, absolute paths like /absolute/path are relative to current drive
        # Keep them as-is for consistency
        if p.is_absolute():
            return p
        return (self.cwd / p).resolve()
    
    @property
    def project_name(self) -> str:
        """Get project name from config or fallback to directory name."""
        if self.config and self.config.project_name:
            return self.config.project_name
        return self.cwd.name
    
    def child(
        self,
        cwd: Optional[Path | str] = None,
        env: Optional[dict[str, str]] = None,
        dry_run: Optional[bool] = None,
        verbose: Optional[bool] = None,
        **kwargs: Any,
    ) -> ExecutionContext:
        """
        Create a child context with overridden values.
        
        Child inherits all parent values, but can override specific ones.
        Environment variables are merged (child overrides parent).
        """
        new_cwd = self.cwd
        if cwd is not None:
            new_cwd = Path(cwd) if isinstance(cwd, str) else cwd
            if not new_cwd.is_absolute():
                new_cwd = (self.cwd / new_cwd).resolve()
        
        new_env = self.env.copy()
        if env:
            new_env.update(env)
        
        return ExecutionContext(
            cwd=new_cwd,
            config=self.config,
            env=new_env,
            dry_run=dry_run if dry_run is not None else self.dry_run,
            verbose=verbose if verbose is not None else self.verbose,
            timeout=kwargs.get("timeout", self.timeout),
            retries=kwargs.get("retries", self.retries),
            stream_callback=kwargs.get("stream_callback", self.stream_callback),
            _template_engine=self._template_engine,
        )

    @classmethod
    def create(
        cls,
        cwd: Optional[Path | str] = None,
        config: Optional[SindriConfig] = None,
        **kwargs: Any,
    ) -> ExecutionContext:
        """
        Factory method to create an execution context.
        
        Args:
            cwd: Working directory (defaults to current directory)
            config: Sindri configuration
            **kwargs: Additional context options
            
        Returns:
            New ExecutionContext instance
        """
        if cwd is None:
            cwd = Path.cwd()
        elif isinstance(cwd, str):
            cwd = Path(cwd)
        
        return cls(cwd=cwd, config=config, **kwargs)
