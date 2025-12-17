"""Shell command execution utilities."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Callable, Optional

from sindri.core.result import CommandResult


async def run_shell_command(
    command_id: str,
    shell: str,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
    dry_run: bool = False,
    stream_callback: Callable[[str, str], None] | None = None,
) -> CommandResult:
    """
    Execute a shell command asynchronously.
    
    Args:
        command_id: Command identifier for result tracking
        shell: Shell command to execute
        cwd: Working directory
        env: Environment variables (merged with system env)
        timeout: Timeout in seconds
        dry_run: If True, don't actually execute
        stream_callback: Optional callback for streaming output (line, stream_type)
        
    Returns:
        CommandResult with execution details
    """
    import time

    start_time = time.time()

    if dry_run:
        return CommandResult(
            command_id=command_id,
            exit_code=0,
            stdout=f"[DRY RUN] Would execute: {shell}",
            duration=0.0,
        )

    # Prepare environment
    full_env = dict(os.environ)
    if env:
        full_env.update(env)

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    try:
        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            shell,
            cwd=str(cwd),
            env=full_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1024 * 1024,  # 1MB buffer
        )

        async def read_stream(
            stream: asyncio.StreamReader,
            stream_type: str,
            lines: list[str],
        ) -> None:
            """Read stream line by line."""
            while True:
                line = await stream.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="replace").rstrip()
                lines.append(line_str)
                if stream_callback:
                    stream_callback(line_str, stream_type)

        # Read both streams concurrently
        await asyncio.gather(
            read_stream(process.stdout, "stdout", stdout_lines),
            read_stream(process.stderr, "stderr", stderr_lines),
        )

        # Wait for process with timeout
        if timeout:
            try:
                exit_code = await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return CommandResult(
                    command_id=command_id,
                    exit_code=124,
                    stdout="\n".join(stdout_lines),
                    stderr="\n".join(stderr_lines),
                    error=f"Command timed out after {timeout}s",
                    duration=time.time() - start_time,
                )
        else:
            exit_code = await process.wait()

        return CommandResult(
            command_id=command_id,
            exit_code=exit_code,
            stdout="\n".join(stdout_lines),
            stderr="\n".join(stderr_lines),
            duration=time.time() - start_time,
        )

    except Exception as e:
        return CommandResult(
            command_id=command_id,
            exit_code=1,
            stdout="\n".join(stdout_lines),
            stderr="\n".join(stderr_lines),
            error=str(e),
            duration=time.time() - start_time,
        )


async def run_shell_commands_parallel(
    commands: list[tuple[str, str, Path]],
    env: dict[str, str] | None = None,
    timeout: int | None = None,
    stream_callback: Callable[[str, str], None] | None = None,
) -> list[CommandResult]:
    """
    Execute multiple shell commands in parallel.
    
    Args:
        commands: List of (command_id, shell, cwd) tuples
        env: Shared environment variables
        timeout: Shared timeout
        stream_callback: Optional callback for streaming output
        
    Returns:
        List of CommandResults in same order as input
    """
    tasks = [
        run_shell_command(
            command_id=cmd_id,
            shell=shell,
            cwd=cwd,
            env=env,
            timeout=timeout,
            stream_callback=stream_callback,
        )
        for cmd_id, shell, cwd in commands
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to error results
    final_results: list[CommandResult] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            cmd_id = commands[i][0]
            final_results.append(
                CommandResult(
                    command_id=cmd_id,
                    exit_code=1,
                    error=f"Exception: {result}",
                )
            )
        else:
            final_results.append(result)

    return final_results
