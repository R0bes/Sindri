"""Shell command execution utilities."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Callable

import structlog

from sindri.core.result import CommandResult

logger = structlog.get_logger(__name__)


async def run_shell_command(
    command_id: str,
    shell: str,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
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
        stream_callback: Callback for streaming output (line, stream_type)
        
    Returns:
        CommandResult with execution details
    """
    start_time = datetime.now()
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    # Merge environment
    full_env = dict(os.environ)
    if env:
        full_env.update(env)

    logger.debug(
        "Executing shell command",
        command_id=command_id,
        shell=shell,
        cwd=str(cwd),
        has_env=env is not None,
        env_keys=len(full_env),
        virtual_env=full_env.get("VIRTUAL_ENV"),
        path_first=full_env.get("PATH", "").split(os.pathsep)[0] if full_env.get("PATH") else None,
    )

    try:
        # Create process
        process = await asyncio.create_subprocess_shell(
            shell,
            cwd=str(cwd),
            env=full_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1024 * 1024,  # 1MB buffer
        )
        
        logger.debug("Process created", command_id=command_id, pid=process.pid)

        async def read_stream(
            stream: asyncio.StreamReader,
            stream_type: str,
            lines: list[str],
        ) -> None:
            """Read from stream line by line."""
            while True:
                line = await stream.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="replace").rstrip()
                lines.append(line_str)
                if stream_callback:
                    prefix = f"[{command_id}]"
                    stream_callback(f"{prefix} {line_str}", stream_type)

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
                duration = (datetime.now() - start_time).total_seconds()
                return CommandResult(
                    command_id=command_id,
                    exit_code=124,
                    stdout="\n".join(stdout_lines),
                    stderr="\n".join(stderr_lines),
                    error=f"Command timed out after {timeout}s",
                    duration=duration,
                )
        else:
            exit_code = await process.wait()

        duration = (datetime.now() - start_time).total_seconds()
        
        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)
        
        logger.debug(
            "Command completed",
            command_id=command_id,
            exit_code=exit_code,
            duration=duration,
            stdout_lines=len(stdout_lines),
            stderr_lines=len(stderr_lines),
            stdout_preview=stdout_text[:200] if stdout_text else None,
            stderr_preview=stderr_text[:200] if stderr_text else None,
        )

        return CommandResult(
            command_id=command_id,
            exit_code=exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
            duration=duration,
        )

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return CommandResult(
            command_id=command_id,
            exit_code=1,
            error=f"Command execution failed: {str(e)}",
            duration=duration,
        )


async def run_shell_commands_parallel(
    commands: list[tuple[str, str, Path, dict[str, str] | None]],
    timeout: int | None = None,
    stream_callback: Callable[[str, str], None] | None = None,
) -> list[CommandResult]:
    """
    Execute multiple shell commands in parallel.
    
    Args:
        commands: List of (command_id, shell, cwd, env) tuples
        timeout: Timeout in seconds for each command
        stream_callback: Callback for streaming output
        
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
        for cmd_id, shell, cwd, env in commands
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to error results
    final_results: list[CommandResult] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            cmd_id = commands[i][0]
            final_results.append(
                CommandResult.failure(cmd_id, f"Exception: {str(result)}")
            )
        else:
            final_results.append(result)
    
    return final_results
