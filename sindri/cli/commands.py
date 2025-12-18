"""CLI command implementations."""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.table import Table

from sindri.config import get_config_dir, load_config
from sindri.core import ExecutionContext, CommandResult
from sindri.core.command import CustomCommand
from sindri.utils import setup_logging
from sindri.cli.display import console
from sindri.cli.template import get_default_config_template

import structlog

logger = structlog.get_logger(__name__)

# Create config subcommand group
config_app = typer.Typer(name="config", help="Configuration management commands")


def _init_registry(sindri_config):
    """Initialize the registry with built-in groups and config commands."""
    from sindri.core import reset_registry, get_registry
    
    # Reset to ensure clean state
    reset_registry()
    registry = get_registry()
    
    # Load built-in groups first
    registry.discover_builtin_groups()
    
    # Then load commands from config (these won't override built-in commands)
    registry.load_from_config(sindri_config)
    
    return registry


@config_app.command("init")
def config_init(
    config_file: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file (default: pyproject.toml if exists, otherwise .sindri/sindri.toml)",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Use interactive mode to detect and configure commands",
    ),
) -> None:
    """Initialize a new Sindri configuration file."""
    cwd = Path.cwd()
    
    if config_file:
        config_path = Path(config_file).resolve()
    else:
        # Default: prefer pyproject.toml if it exists, otherwise .sindri/sindri.toml
        pyproject_path = cwd / "pyproject.toml"
        if pyproject_path.exists():
            config_path = pyproject_path
        else:
            sindri_dir = cwd / ".sindri"
            sindri_dir.mkdir(exist_ok=True)
            console.print("[green]✓[/green] Created .sindri directory")
            config_path = sindri_dir / "sindri.toml"
    
    config_path = config_path.resolve()

    # Check if config already exists
    if config_path.name == "pyproject.toml":
        try:
            import tomllib
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
                if "tool" in data and "sindri" in data["tool"]:
                    if not typer.confirm(f"[tool.sindri] already exists in {config_path}. Overwrite?"):
                        console.print("[yellow]Cancelled.[/yellow]")
                        raise typer.Exit(0)
        except Exception:
            pass
    elif config_path.exists():
        if not typer.confirm(f"Config file already exists at {config_path}. Overwrite?"):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    config_path.parent.mkdir(parents=True, exist_ok=True)

    if interactive:
        from sindri.cli.interactive_init import interactive_init
        interactive_init(config_path)
    else:
        template = get_default_config_template()
        if config_path.name == "pyproject.toml":
            from sindri.utils.pyproject_updater import add_sindri_config_to_pyproject
            import tomllib
            template_dict = tomllib.loads(template.encode())
            success, error = add_sindri_config_to_pyproject(config_path, template_dict)
            if not success:
                console.print(f"[red]Error:[/red] {error}")
                raise typer.Exit(1)
            console.print(f"[green]✓[/green] Added [tool.sindri] to [bold]{config_path}[/bold]")
        else:
            config_path.write_text(template, encoding="utf-8")
            console.print(f"[green]✓[/green] Created config file at [bold]{config_path}[/bold]")
    
    console.print("\n[bold]Sindri is ready![/bold] Run [bold]sindri[/bold] to list commands.")


def init(
    config_file: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file (default: sindri.toml in current directory)",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Use interactive mode to detect and configure commands",
    ),
) -> None:
    """Initialize a new Sindri configuration file (alias for 'config init')."""
    config_init(config_file, interactive=interactive)


@config_app.command("validate")
def config_validate(
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation information",
    ),
) -> None:
    """Validate a Sindri configuration file."""
    try:
        config_path = Path(config).resolve() if config else None
        start_path = Path.cwd()
        sindri_config = load_config(config_path, start_path)

        console.print("[green][OK][/green] Configuration is valid")

        if verbose:
            console.print(f"\n[bold]Config file:[/bold] {sindri_config._config_path}")
            console.print(f"[bold]Workspace:[/bold] {sindri_config._workspace_dir}")
            console.print(f"[bold]Version:[/bold] {sindri_config.version}")
            console.print(f"[bold]Project name:[/bold] {sindri_config.project_name or 'Not set'}")
            console.print(f"[bold]Commands:[/bold] {len(sindri_config.commands)}")
            console.print(f"[bold]Groups:[/bold] {len(sindri_config.groups) if sindri_config.groups else 0}")

            if sindri_config.groups:
                console.print("\n[bold]Groups:[/bold]")
                for group in sindri_config.groups:
                    commands_in_group = sindri_config.get_commands_by_group(group.id)
                    console.print(f"  - {group.title} ({len(commands_in_group)} commands)")

    except FileNotFoundError as e:
        console.print(f"[red][FAIL][/red] [red]Error:[/red] {e}")
        console.print("\nRun [bold]sindri config init[/bold] to create a config file.")
        raise typer.Exit(1)

    except ValueError as e:
        console.print(f"[red][FAIL][/red] [red]Validation failed:[/red] {e}")
        if verbose:
            import traceback
            console.print("\n[dim]Traceback:[/dim]")
            console.print(traceback.format_exc())
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red][FAIL][/red] [red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback
            console.print("\n[dim]Traceback:[/dim]")
            console.print(traceback.format_exc())
        raise typer.Exit(1)


def run(
    command_parts: List[str],
    config: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
    timeout: Optional[int] = None,
    retries: int = 0,
    parallel: bool = False,
) -> None:
    """
    Run one or more commands non-interactively.

    Examples:
        sindri docker up          # Run docker-up command
        sindri d up               # Same, using alias
        sindri compose up         # Run compose-up command
        sindri c up               # Same, using alias
        sindri git commit         # Run git-commit command
        sindri g commit           # Same, using alias
        sindri setup              # Run setup command
        sindri docker up compose down  # Run multiple commands
    """
    # Setup logging with verbose flag
    setup_logging(json_logs=json_logs, verbose=verbose)

    try:
        # Load config
        config_path = Path(config).resolve() if config else None
        start_path = Path.cwd()
        sindri_config = load_config(config_path, start_path)

        # Initialize registry
        registry = _init_registry(sindri_config)

        # Parse command parts
        filtered_parts = []
        for part in command_parts:
            if not part.startswith("-"):
                filtered_parts.append(part)

        # Extract flags for version bump command
        bump_type = None
        if "version" in filtered_parts or "v" in filtered_parts:
            for part in command_parts:
                if part == "--major":
                    bump_type = "major"
                    break
                elif part == "--minor":
                    bump_type = "minor"
                    break
                elif part == "--patch":
                    bump_type = "patch"
                    break
        
        # Resolve commands from registry
        commands = []
        i = 0
        while i < len(filtered_parts):
            # Try two-part command first (e.g., "docker build")
            if i + 1 < len(filtered_parts):
                cmd = registry.resolve_parts([filtered_parts[i], filtered_parts[i + 1]])
                if cmd:
                    commands.append(cmd)
                    i += 2
                    continue
            
            # Try single-part command
            cmd = registry.resolve_parts([filtered_parts[i]])
            if cmd:
                commands.append(cmd)
                i += 1
            else:
                console.print(f"[red]Error:[/red] Unknown command: {filtered_parts[i]}")
                raise typer.Exit(1)

        if not commands:
            console.print("[red]Error:[/red] No valid commands found")
            raise typer.Exit(1)

        # Get config directory
        config_dir = get_config_dir(sindri_config)
        logger.debug("Resolved config directory", config_dir=str(config_dir))

        # Create execution context
        ctx = ExecutionContext(
            cwd=config_dir,
            config=sindri_config,
            dry_run=dry_run,
            verbose=verbose,
            timeout=timeout,
            retries=retries,
        )
        logger.debug("Created execution context", cwd=str(ctx.cwd), dry_run=dry_run, verbose=verbose)

        # Stream callback
        def stream_callback(line: str, stream_type: str) -> None:
            if stream_type == "stderr":
                console.print(f"[red]{line}[/red]")
            else:
                console.print(f"[cyan]{line}[/cyan]")

        ctx.stream_callback = stream_callback
        
        # Run commands
        results = []
        for i, cmd in enumerate(commands):
            logger.debug("Executing command", index=i, command_id=cmd.id, total_commands=len(commands))
            
            # Check if this is a CustomCommand
            if isinstance(cmd, CustomCommand):
                logger.debug("Command is CustomCommand", command_id=cmd.id)
                # Execute custom command with context
                cmd_kwargs = {}
                if hasattr(cmd, 'id') and cmd.id == "version bump" and bump_type:
                    cmd_kwargs["bump_type"] = bump_type
                
                result = asyncio.run(cmd.execute(ctx, **cmd_kwargs))
            else:
                logger.debug("Command is ShellCommand", command_id=cmd.id)
                # Execute shell command
                result = asyncio.run(cmd.execute(ctx))
            
            logger.debug("Command result", command_id=cmd.id, exit_code=result.exit_code, success=result.success)
            results.append(result)
            
            if not result.success and not parallel:
                logger.debug("Command failed, stopping execution", command_id=cmd.id)
                break

        # Print results
        _print_results(results)

        # Exit with appropriate code
        if not all(r.success for r in results):
            exit_code = next((r.exit_code for r in results if not r.success), 1)
            raise typer.Exit(exit_code)

    except typer.Exit:
        raise
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun [bold]sindri init[/bold] to create a config file.")
        raise typer.Exit(1)
    except Exception as e:
        logger.error("Command execution failed", error=str(e))
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


def _print_results(results: List[CommandResult]) -> None:
    """Print command results in a table."""
    from rich.box import ASCII
    from rich.text import Text

    table = Table(
        title="Command Results",
        box=ASCII,
        border_style="cyan",
    )
    table.add_column("Output")

    for result in results:
        def escape_brackets(text: str) -> str:
            if not text:
                return ""
            return text.replace("[", "\\[").replace("]", "\\]")
        
        raw_content = ""
        content_style = "cyan"
        
        has_stderr = result.stderr and result.stderr.strip()
        has_stdout = result.stdout and result.stdout.strip()
        
        if has_stdout:
            raw_content = result.stdout
            content_style = "cyan"
            if has_stderr:
                raw_content = result.stdout + "\n" + result.stderr
        elif has_stderr:
            raw_content = result.stderr
            content_style = "red"
        elif result.error:
            raw_content = f"Error: {result.error}"
            content_style = "red"
        else:
            raw_content = "SUCCESS" if result.success else "FAILED"
            content_style = "green" if result.success else "red"
        
        # Truncate
        raw_lines = raw_content.split("\n")
        if len(raw_lines) > 15:
            truncated_raw = f"... ({len(raw_lines) - 15} lines omitted)\n" + "\n".join(raw_lines[-15:])
        else:
            truncated_raw = raw_content
        
        escaped_content = escape_brackets(truncated_raw)
        output_text = Text(escaped_content, style=content_style)
        table.add_row(output_text)

        console.print(table)


def list_commands(
    config: Optional[str] = None,
) -> None:
    """List all available commands."""
    try:
        config_path = Path(config).resolve() if config else None
        sindri_config = load_config(config_path, Path.cwd())
        
        # Initialize registry to get all commands
        registry = _init_registry(sindri_config)
        
        # Print using registry data
        _print_registry_commands(registry)

    except typer.Exit:
        raise
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun [bold]sindri init[/bold] to create a config file.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


def _print_registry_commands(registry) -> None:
    """Print commands from registry grouped by group."""
    from rich.table import Table

    console.print("[bold]Available Commands[/bold]\n")

    # Collect all commands and their group_ids
    commands_by_group: dict[str | None, list] = {}
    for cmd in registry.iter_commands():
        group_id = getattr(cmd, 'group_id', None)
        if group_id not in commands_by_group:
            commands_by_group[group_id] = []
        commands_by_group[group_id].append(cmd)
    
    # Group commands by group_id
    first_group = True
    for group in sorted(registry.iter_groups(), key=lambda g: g.order or 999):
        if not group.get_commands():
            continue

        if not first_group:
            console.print()  # Empty line between groups
        
        # Compact group header: title and description on same line
        if group.description:
            desc = group.description
            if "(" in desc and ")" in desc:
                last_open = desc.rfind("(")
                if last_open > 0:
                    desc = desc[:last_open].rstrip()
            console.print(f"[bold cyan]{group.title}[/bold cyan] [dim]{desc}[/dim]")
        else:
            console.print(f"[bold cyan]{group.title}[/bold cyan]")

        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column("Command", style="green", no_wrap=True, min_width=20, max_width=35)
        table.add_column("Description", overflow="fold")

        for cmd in group.get_commands():
            # Format command ID for display using the formatting function
            from sindri.cli.parsing import (
                format_command_id_for_display,
                NAMESPACE_ALIASES,
                ACTION_ALIASES,
            )
            cmd_display = format_command_id_for_display(cmd.id)
            
            # Find aliases for namespace and action separately
            namespace = None
            action = None
            namespace_aliases = []
            action_alias = None
            
            # Extract namespace and action from command ID
            has_namespace_prefix = False
            
            if "-" in cmd.id:
                parts = cmd.id.split("-", 1)
                potential_namespace = parts[0]
                # Check if first part is a known namespace
                if potential_namespace in NAMESPACE_ALIASES.values() or potential_namespace in NAMESPACE_ALIASES:
                    has_namespace_prefix = True
                    namespace = potential_namespace
                    action = parts[1]
            elif " " in cmd.id:
                parts = cmd.id.split(" ", 1)
                potential_namespace = parts[0]
                if potential_namespace in NAMESPACE_ALIASES.values() or potential_namespace in NAMESPACE_ALIASES:
                    has_namespace_prefix = True
                    namespace = potential_namespace
                    action = parts[1]
            
            # If no namespace prefix, use group_id as namespace (for commands like "test" in quality group)
            if not has_namespace_prefix:
                # Check if group_id is a known namespace
                if group.id in NAMESPACE_ALIASES.values() or group.id in NAMESPACE_ALIASES:
                    namespace = group.id
                    action = cmd.id
                    # Format as namespace command for display
                    cmd_display = f"{namespace} {action}"
            
            # Show aliases if we have a namespace
            if namespace and action:
                # Resolve namespace: if it's an alias, get the full name
                full_namespace = NAMESPACE_ALIASES.get(namespace, namespace)
                
                # Find all aliases for this namespace (exclude the namespace itself)
                namespace_aliases = [
                    alias
                    for alias, full_ns in NAMESPACE_ALIASES.items()
                    if full_ns == full_namespace and alias != namespace
                ]
                
                # Find action alias (reverse lookup: action might be the value)
                for alias, full_action in ACTION_ALIASES.items():
                    if full_action == action:
                        action_alias = alias
                        break
            
            # Format command with aliases inline
            if namespace_aliases or action_alias:
                # Split the formatted display into namespace and action
                parts = cmd_display.split(" ", 1)
                if len(parts) == 2:
                    ns_part, action_part = parts
                    # Add namespace aliases after namespace
                    if namespace_aliases:
                        ns_aliases_str = ", ".join(namespace_aliases)
                        ns_part = f"{ns_part} ({ns_aliases_str})"
                    # Add action alias after action
                    if action_alias:
                        action_part = f"{action_part} ({action_alias})"
                    cmd_display = f"{ns_part} {action_part}"
            
            desc = cmd.description or ""
            table.add_row(cmd_display, desc)

        console.print(table)
        first_group = False
    
    # Show ungrouped commands (commands without group_id or not in any group)
    ungrouped_commands = []
    for cmd in registry.iter_commands():
        group_id = getattr(cmd, 'group_id', None)
        # Check if command is not in any registered group
        if group_id is None or group_id not in registry.groups:
            # Check if command is not already shown in a group
            found_in_group = False
            for group in registry.iter_groups():
                if cmd.id in [c.id for c in group.get_commands()]:
                    found_in_group = True
                    break
            if not found_in_group:
                ungrouped_commands.append(cmd)
    
    if ungrouped_commands:
        if not first_group:
            console.print()  # Empty line before ungrouped commands
        
        console.print("[bold cyan]Commands[/bold cyan]")
        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column("Command", style="green", no_wrap=True, min_width=18, max_width=35)
        table.add_column("Description", overflow="fold")
        
        for cmd in ungrouped_commands:
            from sindri.cli.parsing import format_command_id_for_display
            cmd_display = format_command_id_for_display(cmd.id)
            desc = cmd.description or ""
            table.add_row(cmd_display, desc)
        
        console.print(table)


def main(
    config: Optional[str] = None,
) -> None:
    """Sindri - A project-configurable command palette for common dev workflows."""
    try:
        config_path = None
        if config:
            config_path = Path(config).resolve()
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
        
        start_path = config_path.parent if config_path else Path.cwd()
        sindri_config = load_config(config_path, start_path)
        
        # Initialize registry and print commands
        registry = _init_registry(sindri_config)
        _print_registry_commands(registry)

    except typer.Exit:
        raise
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun [bold]sindri init[/bold] to create a config file.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
