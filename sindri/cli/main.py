"""Main entry point that handles unknown commands."""

import sys
from pathlib import Path
from typing import Optional

import typer

from sindri.cli.app import app
from sindri.cli.commands import run as run_command
from sindri.cli.display import console
from sindri.cli.parsing import (
    NAMESPACE_ALIASES,
    find_command_by_parts,
    format_command_id_for_display,
)
from sindri.config import load_config


def _parse_args() -> tuple[list[str], Optional[str]]:
    """Parse command-line arguments, extracting command parts and config."""
    args = sys.argv[1:]
    command_parts = []
    skip_next = False
    config = None

    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        # Only treat -c as config if it's before any command parts
        # If -c comes after command parts, treat it as coverage option
        if arg in ["--config", "-c"]:
            if len(command_parts) == 0:
                # -c before commands = config option
                skip_next = True
                if i + 1 < len(args):
                    config = args[i + 1]
                continue
            else:
                # -c after commands = coverage option
                command_parts.append(arg)
                continue
        # Keep coverage options and version bump flags to pass to commands
        if arg == "--coverage":
            command_parts.append(arg)
            continue
        if arg in ["--major", "--minor", "--patch"]:
            command_parts.append(arg)
            continue
        if arg.startswith("-"):
            continue
        # Known Typer commands - don't treat as project commands
        if arg not in ["config", "init", "validate", "list", "run"]:
            command_parts.append(arg)
        else:
            # Known Typer command - let Typer handle it
            break

    return command_parts, config


def _is_project_command(
    command_parts: list[str], config: Optional[str]
) -> bool:
    """Check if command_parts represent a valid project command."""
    try:
        config_path = Path(config).resolve() if config else None
        sindri_config = load_config(config_path, Path.cwd())

        # Try to find the command
        cmd = find_command_by_parts(sindri_config, command_parts)
        if cmd:
            return True

        # Also try as single command ID
        if len(command_parts) == 1:
            cmd = sindri_config.get_command_by_id(command_parts[0])
            if cmd:
                return True

        return False
    except (FileNotFoundError, ValueError):  # noqa: BLE001
        # Config not found or invalid - not a project command
        return False


def main() -> None:
    """Main entry point that catches unknown commands."""
    # Parse arguments
    command_parts, config = _parse_args()

    # If we have command parts that aren't known Typer commands,
    # try to run them as project commands
    if command_parts:
        # Check if it's just a namespace without action
        # (e.g., "docker" without "build")
        namespace = command_parts[0]
        namespace = NAMESPACE_ALIASES.get(namespace, namespace)

        # If it's a known namespace and only one part, show help
        if len(command_parts) == 1 and namespace in [
            "sindri",
            "docker",
            "compose",
            "git",
        ]:
            try:
                from collections import defaultdict

                from rich import box
                from rich.table import Table

                config_path = Path(config).resolve() if config else None
                sindri_config = load_config(config_path, Path.cwd())

                # Find group by namespace
                group = next(
                    (
                        g
                        for g in (sindri_config.groups or [])
                        if g.id == namespace
                    ),
                    None,
                )
                if group:
                    # Show commands in this group
                    commands = sindri_config.get_commands_by_group(namespace)

                    console.print(f"\n[bold]{group.title}[/bold]")
                    if group.description:
                        console.print(f"{group.description}\n")

                    # Group commands by shell command (to combine aliases)
                    grouped_commands = defaultdict(list)
                    for cmd in commands:
                        # Use shell command as key for grouping
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

                    for cmd_group in grouped_commands.values():
                        # Collect all display IDs for this group
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
                                if "-" in cmd.primary_id:
                                    action = cmd.primary_id.split("-", 1)[1]
                                    display_ids.append(action)
                                else:
                                    display_ids.append(cmd.primary_id)
                        # Join with comma
                        command_display = ", ".join(display_ids)
                        # Use title from first command
                        cmd_title = (
                            cmd_group[0].title or cmd_group[0].primary_id
                        )
                        cmd_desc = cmd_group[0].description or ""
                        table.add_row(
                            command_display,
                            cmd_title,
                            cmd_desc,
                        )

                    console.print(table)
                    if commands:
                        first_cmd = commands[0]
                        if "-" in first_cmd.primary_id:
                            first_action = first_cmd.primary_id.split("-")[-1]
                        else:
                            first_action = first_cmd.primary_id
                    else:
                        first_action = "up"
                    console.print(
                        f"\nUsage: [bold]sindri {namespace} <command>[/bold]"
                    )
                    console.print(
                        f"Example: [bold]sindri {namespace} "
                        f"{first_action}[/bold]"
                    )
                    return
            except (FileNotFoundError, ValueError):  # noqa: BLE001
                # If showing help fails, continue to try running as command
                pass

        # Check if it's a valid project command (without flags)
        # For version commands, also check without flags
        command_parts_without_flags = [
            p for p in command_parts if p not in ["--major", "--minor", "--patch"]
        ]
        is_valid = _is_project_command(command_parts_without_flags, config)
        
        if is_valid:
            # It's a project command - run it directly (with flags)
            try:
                run_command(
                    command_parts=command_parts,
                    config=config,
                )
                # Command executed successfully - exit cleanly
                # run_command will raise typer.Exit(1) if command failed,
                # so we won't reach here
                sys.exit(0)
            except typer.Exit as e:
                # run_command raised typer.Exit - exit with correct code
                sys.exit(e.exit_code if hasattr(e, "exit_code") else 1)
            except (FileNotFoundError, ValueError, OSError):  # noqa: BLE001
                # Unexpected error - log and exit
                import traceback

                traceback.print_exc()
                sys.exit(1)
        # Not a project command - let Typer handle it
        # (will show "No such command")

    # Fall back to normal Typer handling (for known Typer commands)
    app()


if __name__ == "__main__":
    main()
