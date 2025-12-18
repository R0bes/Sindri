"""Git command group - version control operations."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

from sindri.core.command import CustomCommand, ShellCommand
from sindri.core.group import CommandGroup
from sindri.core.result import CommandResult

if TYPE_CHECKING:
    from sindri.core.context import ExecutionContext


class GitGroup(CommandGroup):
    """Git command group for version control operations."""

    def __init__(self, default_message: Optional[str] = None) -> None:
        """
        Initialize Git command group.

        Args:
            default_message: Default commit message
        """
        super().__init__(
            group_id="git",
            title="Git",
            description="Git version control commands",
            order=5,
        )
        self.default_message = default_message or "Update"
        self._commands = self._create_commands()

    def _create_commands(self) -> list:
        """Create all Git commands."""
        return [
            ShellCommand(
                id="git-status",
                shell="git status",
                title="Status",
                description="Show working tree status",
                group_id=self.id,
            ),
            GitMonitorCommand(),
            GitMonitorRunCommand(),
            GitWorkflowCommand(),
            ShellCommand(
                id="git-add",
                shell="git add -A",
                title="Add All",
                description="Stage all changes",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-commit",
                shell=f"git add -A && git commit -m '{self.default_message}'",
                title="Commit",
                description="Stage and commit all changes",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-push",
                shell="git push",
                title="Push",
                description="Push commits to remote",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-pull",
                shell="git pull",
                title="Pull",
                description="Pull changes from remote",
                group_id=self.id,
            ),
            ShellCommand(
                id="git-log",
                shell="git log --oneline -20",
                title="Log",
                description="Show recent commit history",
                group_id=self.id,
            ),
        ]

    def get_commands(self):
        """Get all commands in this group."""
        return self._commands


class GitMonitorCommand(CustomCommand):
    """Monitor Git status continuously."""

    def __init__(self) -> None:
        super().__init__(
            command_id="git-monitor",
            title="Monitor",
            description="Continuously monitor Git status (updates every 2 seconds)",
            group_id="git",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute git monitor - continuously show git status."""
        from sindri.core.shell_runner import run_shell_command

        ctx.stream_callback("Monitoring Git status... (Press Ctrl+C to stop)\n", "stdout")

        # Track previous status to detect changes
        previous_status = None
        iteration = 0

        try:
            while True:
                # Run git status
                result = await run_shell_command(
                    command_id="git-status",
                    shell="git status --short",
                    cwd=ctx.cwd,
                    env=ctx.get_env(),
                )

                current_status = result.stdout.strip()

                # Only show if status changed or first iteration
                if current_status != previous_status or iteration == 0:
                    # Clear screen (ANSI escape code)
                    ctx.stream_callback("\033[2J\033[H", "stdout")
                    ctx.stream_callback(f"=== Git Status Monitor (Iteration {iteration + 1}) ===\n", "stdout")
                    ctx.stream_callback(f"Working Directory: {ctx.cwd}\n\n", "stdout")

                    if current_status:
                        ctx.stream_callback("Changes detected:\n", "stdout")
                        for line in current_status.split("\n"):
                            if line.strip():
                                ctx.stream_callback(f"  {line}\n", "stdout")
                    else:
                        ctx.stream_callback("Working tree clean\n", "stdout")

                    # Show branch info
                    branch_result = await run_shell_command(
                        command_id="git-branch",
                        shell="git branch --show-current",
                        cwd=ctx.cwd,
                        env=ctx.get_env(),
                    )
                    branch = branch_result.stdout.strip()
                    if branch:
                        ctx.stream_callback(f"\nCurrent branch: {branch}\n", "stdout")

                    ctx.stream_callback("\nPress Ctrl+C to stop monitoring\n", "stdout")
                    previous_status = current_status

                iteration += 1
                await asyncio.sleep(2)  # Update every 2 seconds

        except KeyboardInterrupt:
            ctx.stream_callback("\n\nMonitoring stopped.\n", "stdout")
            return CommandResult(
                command_id=self.id,
                exit_code=0,
                stdout="Monitoring stopped by user",
            )
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Error monitoring Git status: {str(e)}",
            )


class GitMonitorRunCommand(CustomCommand):
    """Monitor the latest GitHub Actions run after a push."""

    def __init__(self) -> None:
        super().__init__(
            command_id="git-monitor-run",
            title="Monitor Run",
            description="Monitor the latest GitHub Actions workflow run (after push)",
            group_id="git",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute git monitor-run - watch the latest GitHub Actions run."""
        from sindri.core.shell_runner import run_shell_command

        # Check if gh CLI is available
        try:
            check_result = await run_shell_command(
                command_id="gh-check",
                shell="gh --version",
                cwd=ctx.cwd,
                env=ctx.get_env(),
            )
            if not check_result.success:
                return CommandResult(
                    command_id=self.id,
                    exit_code=1,
                    error="GitHub CLI (gh) is not available. Please install it: https://cli.github.com/",
                )
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Error checking GitHub CLI: {str(e)}",
            )

        ctx.stream_callback("Finding latest GitHub Actions run...\n", "stdout")

        # Get the latest run ID
        try:
            # Get JSON output without jq to avoid shell quoting issues
            get_run_result = await run_shell_command(
                command_id="gh-run-list",
                shell="gh run list --limit 1 --json databaseId,status,conclusion,displayTitle",
                cwd=ctx.cwd,
                env=ctx.get_env(),
            )

            if not get_run_result.success:
                error_msg = get_run_result.stderr or get_run_result.error or "Unknown error"
                if "not authenticated" in error_msg.lower() or "authentication" in error_msg.lower():
                    return CommandResult(
                        command_id=self.id,
                        exit_code=1,
                        error="GitHub CLI is not authenticated. Please run: gh auth login",
                    )
                return CommandResult(
                    command_id=self.id,
                    exit_code=1,
                    error=f"Failed to get GitHub Actions runs: {error_msg}",
                )

            if not get_run_result.stdout.strip():
                return CommandResult(
                    command_id=self.id,
                    exit_code=1,
                    error="No GitHub Actions runs found. Make sure you're in a Git repository with GitHub Actions configured.",
                )

            # Parse the run ID from JSON (array with one element)
            import json
            try:
                # Output is a JSON array, get first element
                runs = json.loads(get_run_result.stdout.strip())
                if not runs or len(runs) == 0:
                    return CommandResult(
                        command_id=self.id,
                        exit_code=1,
                        error="No GitHub Actions runs found. Make sure you're in a Git repository with GitHub Actions configured.",
                    )
                run_data = runs[0]  # Get first run from array
                run_id = str(run_data.get("databaseId", ""))
                status = run_data.get("status", "unknown")
                conclusion = run_data.get("conclusion", "")
                title = run_data.get("displayTitle", "Unknown")

                if not run_id:
                    return CommandResult(
                        command_id=self.id,
                        exit_code=1,
                        error="Could not determine run ID from GitHub CLI output.",
                    )

                ctx.stream_callback(f"Found run: {title}\n", "stdout")
                ctx.stream_callback(f"Status: {status} {f'({conclusion})' if conclusion else ''}\n", "stdout")
                ctx.stream_callback(f"Run ID: {run_id}\n\n", "stdout")

                # If already completed, just show the result
                if status == "completed":
                    ctx.stream_callback("Run is already completed. Showing details...\n\n", "stdout")
                    view_result = await run_shell_command(
                        command_id="gh-run-view",
                        shell=f"gh run view {run_id}",
                        cwd=ctx.cwd,
                        env=ctx.get_env(),
                    )
                    # Show the view output
                    if view_result.stdout:
                        ctx.stream_callback(view_result.stdout + "\n", "stdout")
                    if view_result.stderr:
                        ctx.stream_callback(view_result.stderr + "\n", "stderr")
                    
                    # Show conclusion
                    if conclusion == "success":
                        ctx.stream_callback("\n✅ Run completed successfully!\n", "stdout")
                    elif conclusion == "failure":
                        ctx.stream_callback("\n❌ Run failed. Check the details above.\n", "stderr")
                    elif conclusion == "cancelled":
                        ctx.stream_callback("\n⚠️  Run was cancelled.\n", "stderr")
                    else:
                        ctx.stream_callback(f"\n⚠️  Run completed with conclusion: {conclusion}\n", "stderr")
                    
                    return CommandResult(
                        command_id=self.id,
                        exit_code=0 if conclusion == "success" else 1,
                        stdout=view_result.stdout or f"Run {run_id} completed with conclusion: {conclusion}",
                        stderr=view_result.stderr,
                    )

                # Watch the run
                ctx.stream_callback(f"Watching run {run_id}... (Press Ctrl+C to stop)\n\n", "stdout")

                # Use gh run watch with streaming
                watch_result = await run_shell_command(
                    command_id="gh-run-watch",
                    shell=f"gh run watch {run_id} --exit-status",
                    cwd=ctx.cwd,
                    env=ctx.get_env(),
                    stream_callback=ctx.stream_callback,
                )

                return CommandResult(
                    command_id=self.id,
                    exit_code=watch_result.exit_code,
                    stdout=watch_result.stdout,
                    stderr=watch_result.stderr,
                )

            except json.JSONDecodeError:
                return CommandResult(
                    command_id=self.id,
                    exit_code=1,
                    error="Could not parse GitHub CLI output. Make sure you're authenticated: gh auth login",
                )

        except KeyboardInterrupt:
            ctx.stream_callback("\n\nMonitoring stopped.\n", "stdout")
            return CommandResult(
                command_id=self.id,
                exit_code=0,
                stdout="Monitoring stopped by user",
            )
        except Exception as e:
            return CommandResult(
                command_id=self.id,
                exit_code=1,
                error=f"Error monitoring GitHub Actions run: {str(e)}",
            )


class GitWorkflowCommand(CustomCommand):
    """Execute full Git workflow: add, commit, push, and monitor run."""

    def __init__(self) -> None:
        super().__init__(
            command_id="git-workflow",
            title="Workflow",
            description="Execute full workflow: add, commit, push, and monitor GitHub Actions run",
            group_id="git",
        )

    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute git workflow - add, commit, push, and monitor run."""
        from sindri.core.shell_runner import run_shell_command

        results = []
        commit_message = ctx.config.project_name if ctx.config else "Update"

        # Step 1: Add all changes
        ctx.stream_callback("Step 1/4: Staging all changes...\n", "stdout")
        add_result = await run_shell_command(
            command_id="git-add",
            shell="git add -A",
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )
        results.append(("add", add_result))
        if not add_result.success:
            return CommandResult(
                command_id=self.id,
                exit_code=add_result.exit_code,
                stdout="\n".join([f"{step}: {r.stdout}" for step, r in results]),
                stderr="\n".join([f"{step}: {r.stderr}" for step, r in results if r.stderr]),
                error=f"Failed at step 'add': {add_result.error or 'Unknown error'}",
            )

        # Step 2: Commit
        ctx.stream_callback(f"\nStep 2/4: Committing changes with message '{commit_message}'...\n", "stdout")
        commit_result = await run_shell_command(
            command_id="git-commit",
            shell=f"git commit -m '{commit_message}'",
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )
        results.append(("commit", commit_result))
        if not commit_result.success:
            # Check if there's nothing to commit
            if "nothing to commit" in commit_result.stdout.lower() or "nothing to commit" in commit_result.stderr.lower():
                ctx.stream_callback("Nothing to commit, skipping commit step.\n", "stdout")
            else:
                return CommandResult(
                    command_id=self.id,
                    exit_code=commit_result.exit_code,
                    stdout="\n".join([f"{step}: {r.stdout}" for step, r in results]),
                    stderr="\n".join([f"{step}: {r.stderr}" for step, r in results if r.stderr]),
                    error=f"Failed at step 'commit': {commit_result.error or 'Unknown error'}",
                )

        # Step 3: Push
        ctx.stream_callback("\nStep 3/4: Pushing to remote...\n", "stdout")
        push_result = await run_shell_command(
            command_id="git-push",
            shell="git push",
            cwd=ctx.cwd,
            env=ctx.get_env(),
            stream_callback=ctx.stream_callback,
        )
        results.append(("push", push_result))
        if not push_result.success:
            return CommandResult(
                command_id=self.id,
                exit_code=push_result.exit_code,
                stdout="\n".join([f"{step}: {r.stdout}" for step, r in results]),
                stderr="\n".join([f"{step}: {r.stderr}" for step, r in results if r.stderr]),
                error=f"Failed at step 'push': {push_result.error or 'Unknown error'}",
            )

        # Step 4: Monitor run
        ctx.stream_callback("\nStep 4/4: Monitoring GitHub Actions run...\n", "stdout")
        monitor_cmd = GitMonitorRunCommand()
        monitor_result = await monitor_cmd.execute(ctx)
        results.append(("monitor-run", monitor_result))

        # Show monitor result if it failed
        if not monitor_result.success:
            if monitor_result.error:
                ctx.stream_callback(f"\n⚠️  Monitoring failed: {monitor_result.error}\n", "stderr")
            if monitor_result.stderr:
                ctx.stream_callback(f"{monitor_result.stderr}\n", "stderr")
            # Don't fail the whole workflow if monitoring fails
            ctx.stream_callback("Monitoring step failed, but workflow completed (add, commit, push succeeded).\n", "stdout")

        # Combine all results
        combined_stdout = "\n".join([f"=== {step.upper()} ===" for step, _ in results])
        combined_stdout += "\n" + "\n".join([f"{step}: {r.stdout}" for step, r in results if r.stdout])
        combined_stderr = "\n".join([f"{step}: {r.stderr}" for step, r in results if r.stderr])

        # Return success if core steps (add, commit, push) succeeded
        # Monitoring failure is not critical
        core_success = all(r.success for step, r in results if step != "monitor-run")
        return CommandResult(
            command_id=self.id,
            exit_code=0 if core_success else 1,
            stdout=combined_stdout,
            stderr=combined_stderr if combined_stderr else None,
            error=None if core_success else "One or more core workflow steps failed",
        )
