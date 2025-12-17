"""CLI command implementations."""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from sindri.config import get_config_dir, load_config
from sindri.config.implemented_commands import get_implemented_commands, is_custom_command
from sindri.utils import setup_logging
from sindri.runner import AsyncExecutionEngine
from sindri.cli.display import console, print_command_list
from sindri.cli.parsing import parse_command_parts
from sindri.cli.template import get_default_config_template

# Create config subcommand group
config_app = typer.Typer(name="config", help="Configuration management commands")


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
            console.print(f"[green]✓[/green] Created .sindri directory")
            config_path = sindri_dir / "sindri.toml"
    
    # Always resolve the path to ensure it's absolute
    config_path = config_path.resolve()

    # Check if config already exists
    if config_path.name == "pyproject.toml":
        # Check if [tool.sindri] already exists
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

    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if interactive:
        from sindri.cli.interactive_init import interactive_init
        interactive_init(config_path)
    else:
        template = get_default_config_template()
        if config_path.name == "pyproject.toml":
            # Add to pyproject.toml under [tool.sindri]
            from sindri.utils.pyproject_updater import add_sindri_config_to_pyproject
            import tomllib
            # Parse template as TOML to get the config dict
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


# Keep old init command as alias for backward compatibility
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

        # If we get here, validation passed
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
    # Set up logging
    logger = setup_logging(json_logs=json_logs, verbose=verbose)

    try:
        # Load config
        config_path = Path(config).resolve() if config else None
        start_path = Path.cwd()
        sindri_config = load_config(config_path, start_path)

        # Check for coverage option for test command
        coverage_requested = False
        filtered_parts = []
        for part in command_parts:
            if part in ["-c", "--coverage"]:
                coverage_requested = True
                # Don't add coverage flags to filtered_parts
            elif not part.startswith("-"):
                filtered_parts.append(part)

        # Extract flags for version bump command before parsing
        bump_type = None
        if "version" in filtered_parts or "v" in filtered_parts:
            # Check for bump flags in original command_parts
            for i, part in enumerate(command_parts):
                if part == "--major":
                    bump_type = "major"
                    # Remove from filtered_parts if present
                    if part in filtered_parts:
                        filtered_parts.remove(part)
                    break
                elif part == "--minor":
                    bump_type = "minor"
                    if part in filtered_parts:
                        filtered_parts.remove(part)
                    break
                elif part == "--patch":
                    bump_type = "patch"
                    if part in filtered_parts:
                        filtered_parts.remove(part)
                    break
        
        # Parse command parts and find commands
        try:
            commands = parse_command_parts(sindri_config, filtered_parts)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

        if not commands:
            console.print("[red]Error:[/red] No valid commands found")
            raise typer.Exit(1)

        # Apply coverage option to test commands
        if coverage_requested:
            for i, cmd in enumerate(commands):
                if cmd.primary_id == "test":
                    # Add coverage flags to pytest command
                    original_shell = cmd.shell
                    # Check if it's a pytest command (could be just "pytest" or "pytest tests/")
                    if "pytest" in original_shell.lower() or original_shell.strip() == "pytest":
                        # Add --cov=sindri and --cov-report=term if not already present
                        if "--cov" not in original_shell:
                            new_shell = original_shell + " --cov=sindri --cov-report=term"
                            # Create a new command with modified shell
                            from sindri.config import Command as ConfigCommand
                            commands[i] = ConfigCommand(
                                id=cmd.id,
                                title=cmd.title,
                                description=cmd.description,
                                shell=new_shell,
                                cwd=cmd.cwd,
                                env=cmd.env,
                                env_profile=cmd.env_profile,
                                tags=cmd.tags,
                                aliases=cmd.aliases,
                                dependencies=cmd.dependencies,
                                watch=cmd.watch,
                                timeout=cmd.timeout,
                                retries=cmd.retries,
                            )
                        elif "--cov-report" not in original_shell:
                            new_shell = original_shell + " --cov-report=term"
                            from sindri.config import Command as ConfigCommand
                            commands[i] = ConfigCommand(
                                id=cmd.id,
                                title=cmd.title,
                                description=cmd.description,
                                shell=new_shell,
                                cwd=cmd.cwd,
                                env=cmd.env,
                                env_profile=cmd.env_profile,
                                tags=cmd.tags,
                                aliases=cmd.aliases,
                                dependencies=cmd.dependencies,
                                watch=cmd.watch,
                                timeout=cmd.timeout,
                                retries=cmd.retries,
                            )

        # Create execution engine
        config_dir = get_config_dir(sindri_config)
        engine = AsyncExecutionEngine(
            config_dir=config_dir,
            config=sindri_config,
            dry_run=dry_run,
            timeout=timeout,
            retries=retries,
        )

        # Stream callback for live output
        def stream_callback(line: str, stream_type: str) -> None:
            """Stream output line by line."""
            if stream_type == "stderr":
                console.print(f"[red]{line}[/red]")
            else:
                console.print(f"[cyan]{line}[/cyan]")

        # Get implemented commands to check for custom commands
        implemented_commands = get_implemented_commands()
        
        # Run commands
        if parallel and len(commands) > 1:
            # Run in parallel
            results = asyncio.run(engine.run_parallel(commands, stream_callback))
        else:
            # Run sequentially
            results = []
            for cmd in commands:
                # Check if this is a custom command (not a ShellCommand)
                impl_cmd = implemented_commands.get(cmd.primary_id)
                if impl_cmd and is_custom_command(impl_cmd):
                    # Parse command arguments
                    cmd_kwargs = {}
                    if cmd.primary_id == "version bump" and bump_type:
                        cmd_kwargs["bump_type"] = bump_type
                    
                    # Execute custom command directly
                    async def run_custom():
                        return await impl_cmd.execute(
                            engine,
                            config_dir,
                            {},
                            stream_callback=stream_callback,
                            **cmd_kwargs,
                        )
                    result = asyncio.run(run_custom())
                else:
                    # Execute as normal ConfigCommand
                    result = asyncio.run(engine.run_command(cmd, stream_callback))
                results.append(result)
                if not result.success and not parallel:
                    # Stop on first failure if not parallel
                    break

        # Print results summary with content
        def format_output(output: str, max_lines: int = 15) -> str:
            """Format output for display, truncating if too long."""
            if not output:
                return ""
            # Split by newlines
            lines = output.split("\n")
            if len(lines) > max_lines:
                # Show last lines (most recent/relevant output)
                omitted_text = f"... ({len(lines) - max_lines} lines omitted)"
                return omitted_text + "\n" + "\n".join(lines[-max_lines:])
            return output

        # Use simple box style for Windows compatibility (no Unicode characters)
        from rich.box import ASCII
        table = Table(
            title="Command Results",
            box=ASCII,  # Use ASCII borders instead of Unicode
            border_style="cyan",
        )
        # Don't set column style - let the Text objects control the color
        table.add_column("Output")

        all_success = True
        for result in results:
            if not result.success:
                all_success = False

            # Combine stdout and stderr, prioritize stderr if present
            # Escape any brackets in the output to avoid Rich markup conflicts
            def escape_brackets(text: str) -> str:
                """Escape square brackets to prevent Rich markup interpretation."""
                if not text:
                    return ""
                return text.replace("[", "\\[").replace("]", "\\]")
            
            # Determine raw content first (before truncation)
            # Priority: stdout (cyan) > stderr (red) > error > status
            raw_content = ""
            content_style = "cyan"  # Default to cyan for stdout
            
            # Check if stderr has actual content (not just whitespace)
            has_stderr = result.stderr and result.stderr.strip()
            has_stdout = result.stdout and result.stdout.strip()
            
            if has_stdout:
                # stdout has priority - use cyan
                raw_content = result.stdout
                content_style = "cyan"
                # Append stderr if present (but keep cyan as main style)
                if has_stderr:
                    raw_content = result.stdout + "\n" + result.stderr
            elif has_stderr:
                # Only stderr - use red
                raw_content = result.stderr
                content_style = "red"
            elif result.error:
                raw_content = f"Error: {result.error}"
                content_style = "red"
            else:
                raw_content = "SUCCESS" if result.success else "FAILED"
                content_style = "green" if result.success else "red"
            
            # Truncate raw content first
            raw_lines = raw_content.split("\n")
            if len(raw_lines) > 15:
                truncated_raw = f"... ({len(raw_lines) - 15} lines omitted)\n" + "\n".join(raw_lines[-15:])
            else:
                truncated_raw = raw_content
            
            # Now escape and apply markup using Text object for reliable styling
            from rich.text import Text
            escaped_content = escape_brackets(truncated_raw)
            # Create Text object with style instead of markup for better reliability
            output_text = Text(escaped_content, style=content_style)
            
            table.add_row(output_text)


        console.print(table)

        # Exit with appropriate code
        # Use the exit code from the first failed command, or 1 if all succeeded
        if not all_success:
            # Find the first failed command's exit code
            exit_code = 1
            for result in results:
                if not result.success:
                    exit_code = result.exit_code
                    break
            raise typer.Exit(exit_code)

    except typer.Exit:
        # Re-raise typer.Exit (normal exit, not an error)
        raise
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun [bold]sindri init[/bold] to create a config file.")
        raise typer.Exit(1)

    except Exception as e:
        logger.error("Command execution failed", error=str(e))
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


def list_commands(
    config: Optional[str] = None,
) -> None:
    """List all available commands."""
    try:
        config_path = Path(config).resolve() if config else None
        sindri_config = load_config(config_path, Path.cwd())
        print_command_list(sindri_config)

    except typer.Exit:
        # Re-raise typer.Exit (normal exit, not an error)
        raise
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun [bold]sindri init[/bold] to create a config file.")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


def main(
    config: Optional[str] = None,
) -> None:
    """Sindri - A project-configurable command palette for common dev workflows."""
    try:
        config_path = None
        if config:
            # Resolve the config path to absolute path
            config_path = Path(config).resolve()
            # Verify the file exists
            if not config_path.exists():
                raise FileNotFoundError(
                    f"Config file not found: {config_path}"
                )
        
        # Use the directory of the config file as start_path if config is provided,
        # otherwise use current working directory
        start_path = config_path.parent if config_path else Path.cwd()
        sindri_config = load_config(config_path, start_path)
        print_command_list(sindri_config)

    except typer.Exit:
        # Re-raise typer.Exit (normal exit, not an error)
        raise
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun [bold]sindri init[/bold] to create a config file.")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

