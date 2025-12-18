"""CLI interface for Sindri."""

from pathlib import Path
from typing import List, Optional

import typer

from sindri.cli.app import app
from sindri.cli.commands import (
    config_app,
    init,
    list_commands,
    main as main_command,
    run as run_command,
)
from sindri.cli.subcommands import register_namespace_subcommands

# Register commands
app.add_typer(config_app)

# Register namespace subcommands (only configured ones)
register_namespace_subcommands(app, Path.cwd())


@app.command("init")
def init_cmd(
    config_file: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file (default: .sindri/sindri.toml or sindri.toml in current directory)",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Use interactive mode to detect and configure commands",
    ),
) -> None:
    """Initialize a new Sindri configuration file (alias for 'config init')."""
    init(config_file, interactive=interactive)


@app.command("run")
def run_cmd(
    command_parts: List[str] = typer.Argument(
        ...,
        help="Command(s) to run (e.g., 'docker up', 'd up', 'compose up', 'c up', 'git commit', 'g commit', 'setup')"
    ),
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be executed without running",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
    json_logs: bool = typer.Option(
        False,
        "--json-logs",
        help="Output logs in JSON format",
    ),
    timeout: Optional[int] = typer.Option(
        None,
        "--timeout",
        "-t",
        help="Timeout in seconds for command execution",
    ),
    retries: int = typer.Option(
        0,
        "--retries",
        "-r",
        help="Number of retries on failure",
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        "-p",
        help="Run multiple commands in parallel",
    ),
) -> None:
    """Run one or more commands non-interactively."""
    run_command(
        command_parts=command_parts,
        config=config,
        dry_run=dry_run,
        verbose=verbose,
        json_logs=json_logs,
        timeout=timeout,
        retries=retries,
        parallel=parallel,
    )


@app.command("list")
def list_cmd(
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """List all available commands."""
    list_commands(config=config)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Sindri - A project-configurable command palette for common dev workflows."""
    if ctx.invoked_subcommand is None:
        # Check if there are command-like arguments
        import sys
        # Get args from sys.argv, but filter out pytest/test-related args
        args = []
        if hasattr(sys, 'argv'):
            raw_args = sys.argv[1:]
            # Filter out pytest/test-related arguments that might appear in test context
            for arg in raw_args:
                # Skip pytest/test arguments
                if arg.startswith("tests/") or "::" in arg or arg.endswith(".py"):
                    continue
                # Skip pytest options
                if arg.startswith("-") and any(x in arg for x in ["pytest", "test", "::"]):
                    continue
                args.append(arg)
        
        # Filter out options, but keep -c/--coverage after commands
        command_args = []
        skip_next = False
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            # Only treat -c as config if it's before any command parts
            if arg in ["--config", "-c"] and len(command_args) == 0:
                skip_next = True
                continue
            # Keep -c/--coverage if it comes after commands
            if arg in ["-c", "--coverage"] and len(command_args) > 0:
                command_args.append(arg)
                continue
            if arg.startswith("-") and arg not in ["-c", "--coverage"]:
                continue
            if arg not in ["config", "init", "validate", "list", "run"]:
                command_args.append(arg)
        
        if command_args:
            # Treat as command parts and run
            run_command(
                command_parts=command_args,
                config=config,
            )
        else:
            # No arguments, show command list
            try:
                main_command(config=config)
            except typer.Exit:
                # Re-raise typer.Exit (normal exit, not an error)
                raise
            except Exception as e:
                # Unexpected error - log and exit
                from sindri.cli.display import console
                console.print(f"[red]Error:[/red] {str(e)}")
                raise typer.Exit(1)


__all__ = ["app"]
