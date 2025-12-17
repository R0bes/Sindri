"""Async execution engine for running commands."""

import asyncio
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from sindri.config import Command, SindriConfig
from sindri.utils import get_logger, get_project_name
from sindri.runner.result import CommandResult

logger = get_logger("runner")


class AsyncExecutionEngine:
    """Async execution engine for running commands."""

    def __init__(
        self,
        config_dir: Path,
        config: Optional[SindriConfig] = None,
        dry_run: bool = False,
        timeout: Optional[int] = None,
        retries: int = 0,
    ):
        self.config_dir = config_dir
        self.config = config
        self.dry_run = dry_run
        self.default_timeout = timeout
        self.default_retries = retries
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.cleanup_hooks: List[Callable[[], None]] = []
        self._shutdown_event = asyncio.Event()

        # Set up signal handlers for graceful shutdown
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, self._handle_shutdown)

    def _expand_templates(self, shell_cmd: str) -> str:
        """Expand template variables in shell command."""
        if not self.config:
            return shell_cmd

        # Get project name from config or derive from directory
        project_name = self.config.project_name or get_project_name(self.config_dir)

        # Get registry from defaults
        registry = "registry.schwende.lan:5000"
        if self.config._defaults and self.config._defaults.docker_registry:
            registry = self.config._defaults.docker_registry

        # Replace templates
        shell_cmd = shell_cmd.replace("{registry}", registry)
        shell_cmd = shell_cmd.replace("${project_name}", project_name)

        return shell_cmd

    def _handle_shutdown(self) -> None:
        """Handle shutdown signal."""
        logger.info("Shutdown signal received, cleaning up...")
        self._shutdown_event.set()
        # Run cleanup hooks
        for hook in self.cleanup_hooks:
            try:
                hook()
            except Exception as e:
                logger.error("Cleanup hook failed", error=str(e))

    def register_cleanup(self, hook: Callable[[], None]) -> None:
        """Register a cleanup hook to run on shutdown."""
        self.cleanup_hooks.append(hook)

    async def run_command(
        self,
        command: Command,
        stream_callback: Optional[Callable[[str, str], None]] = None,
    ) -> CommandResult:
        """
        Run a single command asynchronously.

        Args:
            command: Command to execute
            stream_callback: Optional callback for streaming output (line, stream_type)

        Returns:
            CommandResult with execution details
        """
        if self.dry_run:
            logger.info(
                "DRY RUN: Would execute command",
                command_id=command.id,
                shell=command.shell,
            )
            return CommandResult(command.id, 0, stdout="[DRY RUN] Command not executed")

        start_time = datetime.now()
        timeout = command.timeout or self.default_timeout
        max_retries = (
            command.retries if command.retries is not None else self.default_retries
        )

        # Resolve working directory
        # config_dir is already the project root (get_config_dir handles this)
        cwd = self.config_dir
        if command.cwd:
            cwd = (self.config_dir / command.cwd).resolve()
            if not cwd.exists():
                error_msg = f"Working directory does not exist: {cwd}"
                logger.error(error_msg)
                return CommandResult(command.primary_id, 1, error=error_msg)

        # Prepare environment variables
        # Start with project-level environment variables if env_profile is set
        env: Dict[str, str] = {}
        if self.config and command.env_profile:
            project_env_vars = self.config.get_env_vars(command.env_profile)
            env.update(project_env_vars)

        # Command-specific env vars override project-level vars
        if command.env:
            env.update(command.env)

        # Build shell command and expand templates
        shell_cmd = self._expand_templates(command.shell)

        last_result: Optional[CommandResult] = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info("Retrying command", command_id=command.primary_id, attempt=attempt)
                await asyncio.sleep(1)  # Brief delay before retry

            try:
                result = await self._execute_shell(
                    shell_cmd,
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
                    stream_callback=stream_callback,
                    prefix=f"[{command.primary_id}]",
                )

                duration = (datetime.now() - start_time).total_seconds()
                last_result = CommandResult(
                    command_id=command.primary_id,
                    exit_code=result[0],
                    stdout=result[1],
                    stderr=result[2],
                    duration=duration,
                )

                if last_result.success:
                    logger.info(
                        "Command completed successfully",
                        command_id=command.primary_id,
                        duration=duration,
                    )
                    break
                else:
                    logger.warning(
                        "Command failed",
                        command_id=command.primary_id,
                        exit_code=last_result.exit_code,
                        attempt=attempt + 1,
                    )

            except asyncio.TimeoutError:
                error_msg = f"Command timed out after {timeout}s"
                logger.error(error_msg, command_id=command.primary_id)
                duration = (datetime.now() - start_time).total_seconds()
                last_result = CommandResult(
                    command.primary_id, 124, error=error_msg, duration=duration
                )
                break

            except Exception as e:
                error_msg = f"Command execution failed: {str(e)}"
                logger.error(error_msg, command_id=command.primary_id, error=str(e))
                duration = (datetime.now() - start_time).total_seconds()
                last_result = CommandResult(
                    command.primary_id, 1, error=error_msg, duration=duration
                )
                # Don't retry on exception, break immediately
                break

        if last_result is None:
            last_result = CommandResult(command.primary_id, 1, error="No execution attempted")

        return last_result

    async def _execute_shell(
        self,
        shell_cmd: str,
        cwd: Path,
        env: Dict[str, str],
        timeout: Optional[int],
        stream_callback: Optional[Callable[[str, str], None]],
        prefix: str = "",
    ) -> Tuple[int, str, str]:
        """
        Execute a shell command and stream output.

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []

        # Create process
        process = await asyncio.create_subprocess_shell(
            shell_cmd,
            cwd=str(cwd),
            env={**os.environ, **env} if env else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1024 * 1024,  # 1MB buffer
        )

        # Track process
        task_id = f"proc_{process.pid}"
        self.running_tasks[task_id] = asyncio.create_task(
            self._wait_for_process(process)
        )

        try:
            # Stream output line by line
            async def read_stream(
                stream: asyncio.StreamReader, stream_type: str
            ) -> None:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    line_str = line.decode("utf-8", errors="replace").rstrip()
                    if stream_type == "stdout":
                        stdout_lines.append(line_str)
                    else:
                        stderr_lines.append(line_str)

                    if stream_callback:
                        stream_callback(f"{prefix} {line_str}", stream_type)

            # Read both streams concurrently
            await asyncio.gather(
                read_stream(process.stdout, "stdout"),
                read_stream(process.stderr, "stderr"),
            )

            # Wait for process to complete
            if timeout:
                try:
                    exit_code = await asyncio.wait_for(process.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    raise
            else:
                exit_code = await process.wait()

        finally:
            # Clean up task tracking
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)

        return (exit_code, stdout, stderr)

    async def _wait_for_process(self, process: asyncio.subprocess.Process) -> None:
        """Wait for a process and handle cleanup."""
        try:
            await process.wait()
        except Exception as e:
            logger.error("Error waiting for process", error=str(e))

    async def run_parallel(
        self,
        commands: List[Command],
        stream_callback: Optional[Callable[[str, str], None]] = None,
    ) -> List[CommandResult]:
        """
        Run multiple commands in parallel.

        Args:
            commands: List of commands to execute
            stream_callback: Optional callback for streaming output

        Returns:
            List of CommandResults in the same order as commands
        """
        logger.info("Running commands in parallel", count=len(commands))

        tasks = [self.run_command(cmd, stream_callback) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results: List[CommandResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Command execution raised exception",
                    command_id=commands[i].id,
                    error=str(result),
                )
                final_results.append(
                    CommandResult(commands[i].id, 1, error=f"Exception: {str(result)}")
                )
            else:
                final_results.append(result)

        return final_results

    async def run_with_dependencies(
        self,
        command: Command,
        all_commands: List[Command],
        stream_callback: Optional[Callable[[str, str], None]] = None,
    ) -> CommandResult:
        """
        Run a command with its dependencies (before/after).

        Args:
            command: Command to execute
            all_commands: All available commands (for dependency resolution)
            stream_callback: Optional callback for streaming output

        Returns:
            CommandResult for the main command
        """
        # Run "before" dependencies
        if command.dependencies and command.dependencies.before:
            before_commands = [
                cmd for cmd in all_commands if cmd.primary_id in command.dependencies.before
            ]
            if before_commands:
                logger.info(
                    "Running before dependencies",
                    command_id=command.primary_id,
                    deps=command.dependencies.before,
                )
                await self.run_parallel(before_commands, stream_callback)

        # Run main command
        result = await self.run_command(command, stream_callback)

        # Run "after" dependencies
        if command.dependencies and command.dependencies.after:
            after_commands = [
                cmd for cmd in all_commands if cmd.primary_id in command.dependencies.after
            ]
            if after_commands:
                logger.info(
                    "Running after dependencies",
                    command_id=command.primary_id,
                    deps=command.dependencies.after,
                )
                await self.run_parallel(after_commands, stream_callback)

        return result

