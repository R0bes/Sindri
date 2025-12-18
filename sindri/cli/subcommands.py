"""Dynamic subcommand groups for Typer."""

from collections import defaultdict
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.table import Table

from sindri.cli.commands import run as run_command
from sindri.cli.display import console
from sindri.cli.parsing import format_command_id_for_display, NAMESPACE_ALIASES, ACTION_ALIASES
from sindri.config import load_config


def create_namespace_subcommand(namespace: str) -> typer.Typer:
    """
    Create a dynamic Typer subcommand group for a namespace.

    This allows commands like:
        sindri docker build
        sindri compose up
        sindri git commit

    Args:
        namespace: The namespace name (e.g., "docker", "compose", "git")

    Returns:
        A Typer instance configured as a subcommand group
    """
    namespace_app = typer.Typer(
        name=namespace,
        help=f"{namespace.capitalize()} commands",
        invoke_without_command=True,
    )

    @namespace_app.callback(invoke_without_command=True)
    def namespace_callback(
        ctx: typer.Context,
        action: Optional[str] = typer.Argument(
            None, help="Action to perform"
        ),
        config: Optional[str] = typer.Option(
            None,
            "--config",
            "-c",
            help="Path to config file",
        ),
        major: bool = typer.Option(False, "--major", help="Bump major version"),
        minor: bool = typer.Option(False, "--minor", help="Bump minor version"),
        patch: bool = typer.Option(False, "--patch", help="Bump patch version"),
    ) -> None:
        """Handle namespace commands."""
        # If no action provided, show help
        if ctx.invoked_subcommand is None and action is None:
            try:
                sindri_config = load_config(
                    Path(config) if config else None, Path.cwd()
                )
                groups = sindri_config.groups or []
                group = next(
                    (g for g in groups if g.id == namespace),
                    None,
                )
                if group:
                    commands = sindri_config.get_commands_by_group(namespace)
                    if commands:
                        console.print(f"\n[bold]{group.title}[/bold]")
                        if group.description:
                            console.print(f"{group.description}\n")

                        # Group commands by shell command (to combine aliases)
                        grouped_commands = defaultdict(list)
                        for cmd in commands:
                            key = (cmd.shell, cmd.title or cmd.primary_id)
                            grouped_commands[key].append(cmd)

                        table = Table(
                            box=box.SIMPLE,
                            show_header=True,
                            header_style="bold",
                        )
                        table.add_column("Command", style="cyan", no_wrap=True)
                        table.add_column("Title", style="magenta")
                        table.add_column("Description")

                        for (_shell, _title), cmd_group in (
                            grouped_commands.items()
                        ):
                            display_ids = []
                            first = True
                            for cmd in cmd_group:
                                display_id = format_command_id_for_display(
                                    cmd.primary_id
                                )
                                # For subcommands, only show namespace on first
                                if first:
                                    display_ids.append(display_id)
                                    first = False
                                else:
                                    # Extract action part only
                                    cmd_id = cmd.primary_id
                                    if "-" in cmd_id:
                                        action = cmd_id.split("-", 1)[1]
                                        display_ids.append(action)
                                    else:
                                        display_ids.append(cmd.primary_id)
                            command_display = ", ".join(display_ids)
                            first_cmd = cmd_group[0]
                            cmd_title = first_cmd.title or first_cmd.primary_id
                            cmd_desc = cmd_group[0].description or ""
                            table.add_row(command_display, cmd_title, cmd_desc)

                        console.print(table)
                        raise typer.Exit(0)
            except (FileNotFoundError, ValueError, KeyError):
                # Config not found, invalid, or group not found
                pass

        # If action provided, try to run it
        if action:
            try:
                # Resolve action alias (e.g., "wf" -> "workflow")
                resolved_action = ACTION_ALIASES.get(action, action)
                
                # Get raw args from sys.argv to capture flags
                import sys
                args = sys.argv[1:]
                # Find namespace and action in args, collect everything after
                namespace_idx = -1
                action_idx = -1
                remaining_args = []
                # Build reverse alias map (full -> aliases)
                reverse_aliases = {}
                for alias, full_ns in NAMESPACE_ALIASES.items():
                    if full_ns not in reverse_aliases:
                        reverse_aliases[full_ns] = []
                    reverse_aliases[full_ns].append(alias)
                
                for i, arg in enumerate(args):
                    # Check if arg matches namespace or any of its aliases
                    aliases = reverse_aliases.get(namespace, [])
                    if arg == namespace or arg in aliases:
                        namespace_idx = i
                    elif namespace_idx >= 0 and (arg == action or arg == resolved_action):
                        action_idx = i
                        # Collect everything after action as additional args
                        remaining_args = args[action_idx + 1:]
                        break
                
                command_parts = [namespace, resolved_action] + remaining_args
                run_command(
                    command_parts=command_parts,
                    config=config,
                )
            except Exception as exc:  # noqa: BLE001
                raise typer.Exit(1) from exc

    return namespace_app


def register_namespace_subcommands(
    app: typer.Typer, config_path: Optional[Path] = None
) -> None:
    """
    Register namespace subcommands dynamically based on configuration.

    Only registers namespaces that are actually configured in the config file.
    This is faster because it doesn't load all command groups.

    Args:
        app: The main Typer app to register subcommands on
        config_path: Optional path to config file (for lazy loading)
    """
    # Namespace to alias mapping
    namespace_aliases = {
        "docker": ["d"],
        "compose": ["c"],
        "git": ["g"],
        "sindri": [],
        "version": ["v"],
        "quality": ["q"],
        "application": ["app", "a"],
        "pypi": ["p"],
        "docs": [],
    }

    # Always register built-in namespaces
    always_register = {"version", "git", "docker", "compose", "quality", "application", "pypi", "docs"}

    # Try to load config to see which namespaces are configured
    try:
        sindri_config = load_config(
            config_path, Path.cwd() if not config_path else None
        )
        configured_groups = sindri_config.groups or []
        configured_namespaces = {g.id for g in configured_groups}
        # Add always-registered namespaces
        configured_namespaces.update(always_register)
    except (FileNotFoundError, ValueError, KeyError):
        # If config not found or error, register all known namespaces
        configured_namespaces = {
            "sindri",
            "docker",
            "compose",
            "git",
            "version",
            "quality",
            "application",
            "pypi",
            "docs",
        }

    # Register configured namespaces
    for namespace in configured_namespaces:
        # Create namespace subcommand
        namespace_app = create_namespace_subcommand(namespace)
        app.add_typer(namespace_app, name=namespace)

        # Register aliases if any
        if namespace in namespace_aliases:
            for alias in namespace_aliases[namespace]:
                alias_app = create_namespace_subcommand(namespace)
                app.add_typer(alias_app, name=alias)
