"""Command parsing utilities."""

from typing import List, Optional

from sindri.config import Command, SindriConfig

# Namespace aliases (short -> full)
NAMESPACE_ALIASES = {
    "d": "docker",
    "c": "compose",
    "dc": "docker-compose",
    "g": "git",
    "q": "quality",
    "app": "application",
    "a": "application",
    "v": "version",
    "p": "pypi",
}

# Command action aliases (short -> full)
ACTION_ALIASES = {
    "bp": "build_and_push",
    "wf": "workflow",
}


def resolve_command_id(parts: List[str]) -> Optional[str]:
    """
    Resolve command parts to a command ID.

    Examples:
        ["docker", "up"] -> "docker-up"
        ["d", "up"] -> "docker-up"
        ["compose", "up"] -> "compose-up"
        ["docker", "bp"] -> "docker-build_and_push"
        ["docker-up"] -> "docker-up"
        ["install"] -> "install"
    """
    if not parts:
        return None

    # If single part, return as-is (might be full ID like "docker-up")
    if len(parts) == 1:
        return parts[0]

    # Resolve namespace alias
    namespace = parts[0]
    namespace = NAMESPACE_ALIASES.get(namespace, namespace)

    # Resolve action alias
    action = parts[1]
    action = ACTION_ALIASES.get(action, action)

    # Build command ID: namespace-action
    command_id = f"{namespace}-{action}"

    # If more parts, join them
    if len(parts) > 2:
        remaining_parts = [ACTION_ALIASES.get(p, p) for p in parts[2:]]
        command_id = f"{namespace}-{action}-{'-'.join(remaining_parts)}"

    return command_id


def find_command_by_parts(
    config: SindriConfig, parts: List[str]
) -> Optional[Command]:
    """
    Find a command by parts, trying different combinations.

    Returns:
        Command object or None
    """
    # Try direct resolution
    command_id = resolve_command_id(parts)
    if command_id:
        cmd = config.get_command_by_id(command_id)
        if cmd:
            return cmd

    # Try with namespace aliases
    if len(parts) >= 2:
        for alias, full_name in NAMESPACE_ALIASES.items():
            if parts[0] == alias:
                alt_parts = [full_name] + parts[1:]
                command_id = resolve_command_id(alt_parts)
                if command_id:
                    cmd = config.get_command_by_id(command_id)
                    if cmd:
                        return cmd

    return None


def format_command_id_for_display(command_id: str) -> str:
    """
    Convert command ID to subcommand syntax for display.

    Examples:
        "docker-restart" -> "docker restart"
        "docker-up" -> "docker up"
        "compose-up" -> "compose up"
        "git-commit" -> "git commit"
        "version show" -> "version show"
        "version bump" -> "version bump"
        "pypi-validate" -> "pypi validate"
        "pypi-push" -> "pypi push"
        "setup" -> "setup"
    """
    # Check if ID matches namespace-action pattern with hyphen
    namespaces = [
        "docker",
        "compose",
        "docker-compose",
        "git",
        "pypi",
        "version",
        "setup",
        "app",
        "application",
        "quality",
    ]
    for namespace in namespaces:
        if command_id.startswith(f"{namespace}-"):
            action = command_id[len(namespace) + 1:]
            return f"{namespace} {action}"

    # Check if ID already has space (e.g., "version show", "version bump")
    # These are already in the correct format
    for namespace in ["version"]:
        if command_id.startswith(f"{namespace} "):
            return command_id

    # Return as-is if no namespace match
    return command_id


def parse_command_parts(
    config: SindriConfig, command_parts: List[str]
) -> List[Command]:
    """
    Parse command parts and find matching commands.

    Examples:
        ["docker", "up"] -> [Command(id="docker-up")]
        ["d", "up"] -> [Command(id="docker-up")]
        ["setup"] -> [Command(id="setup")]
        ["docker", "up", "compose", "down"] -> [
            Command(id="docker-up"), Command(id="compose-down")
        ]
        ["version", "bump", "--patch"] -> [
            Command(id="version bump")
        ] (flags ignored)
    """
    commands = []
    i = 0
    # Flags that should be ignored during parsing
    # (passed to commands separately)
    version_bump_flags = ["--major", "--minor", "--patch"]

    while i < len(command_parts):
        # Skip flags during parsing
        if command_parts[i] in version_bump_flags:
            i += 1
            continue

        # Try to find command starting from current position
        found = False

        # Try progressively longer sequences
        for j in range(i + 1, len(command_parts) + 1):
            parts = command_parts[i:j]
            # Skip flags in parts
            parts = [p for p in parts if p not in version_bump_flags]
            if not parts:
                break
            cmd = find_command_by_parts(config, parts)
            if cmd:
                commands.append(cmd)
                i = j
                found = True
                break

        if not found:
            # Try as single command ID or alias
            cmd = config.get_command_by_id(command_parts[i])
            if cmd:
                commands.append(cmd)
                i += 1
            else:
                # Check if it's a flag - if so, skip it
                if command_parts[i] in version_bump_flags:
                    i += 1
                    continue
                raise ValueError(
                    f"Command '{' '.join(command_parts[i:])}' not found"
                )

    return commands
