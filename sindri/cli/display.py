"""Display utilities for CLI output."""

from typing import List, Optional

import sys
import os
from rich.console import Console
from rich.table import Table
from rich.text import Text

from sindri.config import Command, Group, SindriConfig
from sindri.cli.parsing import format_command_id_for_display

# Configure console for Windows compatibility
# On Windows, use safe encoding and disable Unicode box drawing
if os.name == "nt":
    # Set UTF-8 encoding for stdout/stderr on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    
    console = Console(
        force_terminal=True,
        legacy_windows=True,
        safe_box=True,  # Use safe box drawing on Windows
    )
else:
    console = Console()

# Color scheme for different groups
GROUP_COLORS = {
    "sindri": "bright_cyan",
    "general": "bright_blue",
    "quality": "bright_green",
    "application": "bright_yellow",
    "docker": "bright_magenta",
    "compose": "bright_cyan",
    "git": "bright_red",
}

# Default color for unknown groups
DEFAULT_GROUP_COLOR = "cyan"


def format_description(desc: Optional[str], max_length: int = 50) -> str:
    """Format description with truncation if needed."""
    if not desc:
        return ""
    if len(desc) > max_length:
        return desc[:max_length - 3] + "..."
    return desc


def create_command_table(
    config: SindriConfig, organized: List[tuple[Optional[Group], List[Command]]]
) -> Table:
    """
    Create a table displaying commands, optionally grouped.

    Args:
        config: SindriConfig instance
        organized: List of (Group, Commands) tuples from get_commands_organized_by_groups()

    Returns:
        Rich Table instance
    """
    if len(organized) > 1 or (len(organized) == 1 and organized[0][0] is not None):
        # Show grouped - create one table with headers only at top
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("ID", style="bright_cyan", header_style="bold bright_cyan")
        table.add_column("Title", style="bright_white", header_style="bold bright_white")
        table.add_column("Description", style="dim white", header_style="bold dim white")
        table.add_column("Tags", style="bright_yellow", header_style="bold bright_yellow")
        
        # Store group color for dynamic styling
        current_group_color = None

        first_group = True
        for group, commands in organized:
            if not commands:
                continue

            if not first_group:
                # Add empty row as separator
                table.add_row("", "", "", "")

            # Add group header as a row with color based on group ID
            group_title = group.title if group else "Other"
            group_id = group.id if group else "other"
            group_desc = group.description if group and group.description else ""
            
            # Get color for this group
            current_group_color = GROUP_COLORS.get(group_id, DEFAULT_GROUP_COLOR)
            
            # Use Rich Text for group headers to support colors
            # Use ASCII-compatible character for Windows
            group_header = Text(f"> {group_title}", style=f"bold {current_group_color}")
            group_desc_text = Text(group_desc, style=current_group_color) if group_desc else Text("")
            
            table.add_row(
                group_header,
                Text(""),
                group_desc_text,
                Text("")
            )

            # Group commands by shell command (to combine aliases)
            from collections import defaultdict
            grouped_commands = defaultdict(list)
            for cmd in commands:
                # Use shell command as key for grouping
                key = (cmd.shell, cmd.title or cmd.primary_id)
                grouped_commands[key].append(cmd)
            
            # Add commands in this group (grouped by aliases)
            for (shell, title), cmd_group in grouped_commands.items():
                tags_str = ", ".join(cmd_group[0].tags) if cmd_group[0].tags else ""
                desc = format_description(cmd_group[0].description)
                # Collect all display IDs for this group
                display_ids = []
                first = True
                for cmd in cmd_group:
                    display_id = format_command_id_for_display(cmd.primary_id)
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
                
                cmd_title = cmd_group[0].title or cmd_group[0].primary_id
                
                # Use Rich Text for command IDs with group color
                cmd_id_text = Text(command_display, style=current_group_color)
                cmd_title_text = Text(cmd_title, style="bright_white")
                desc_text = Text(desc, style="dim white")
                tags_text = Text(tags_str, style="bright_yellow") if tags_str else Text("")
                
                table.add_row(cmd_id_text, cmd_title_text, desc_text, tags_text)

            first_group = False
    else:
        # Show flat list (no groups)
        table = Table(title="[bold bright_cyan]Available Commands[/bold bright_cyan]")
        table.add_column("ID", style="bright_cyan", header_style="bold bright_cyan")
        table.add_column("Title", style="bright_white", header_style="bold bright_white")
        table.add_column("Description", style="dim white", header_style="bold dim white")
        table.add_column("Tags", style="bright_yellow", header_style="bold bright_yellow")

        for cmd in config.commands:
            tags_str = ", ".join(cmd.tags) if cmd.tags else ""
            desc = format_description(cmd.description)
            display_id = format_command_id_for_display(cmd.id)
            # Use column styles - they will apply automatically
            table.add_row(display_id, cmd.title, desc, tags_str)

    return table


def print_command_list(config: SindriConfig) -> None:
    """Print a formatted list of all commands."""
    organized = config.get_commands_organized_by_groups()
    table = create_command_table(config, organized)
    console.print(table)

