# API Referenz

API-Dokumentation für Entwickler, die Sindri erweitern möchten.

## Core API

### Command Protocol

Alle Commands implementieren das `Command` Protocol:

```python
from sindri.core.command import Command

class MyCommand(Command):
    @property
    def id(self) -> str:
        """Unique command identifier."""
        return "my-command"
    
    @property
    def title(self) -> str:
        """Display title."""
        return "My Command"
    
    async def execute(self, context: ExecutionContext) -> CommandResult:
        """Execute the command."""
        # Implementation
```

### Command Registry

```python
from sindri.core.registry import get_registry

registry = get_registry()
registry.register(my_command)
registry.resolve("my-command")
```

### Execution Context

```python
from sindri.core.context import ExecutionContext

context = ExecutionContext(
    cwd=Path.cwd(),
    env={"VAR": "value"},
    templates={"project": "myproject"}
)
```

### Command Result

```python
from sindri.core.result import CommandResult

result = CommandResult(
    exit_code=0,
    stdout="Output",
    stderr="",
    success=True
)
```

## Config API

### SindriConfig

```python
from sindri.config import SindriConfig, Command, Group

config = SindriConfig(
    version="1.0",
    project_name="my-project",
    commands=[
        Command(id="test", shell="pytest", tags=["test"])
    ],
    groups=[
        Group(id="quality", title="Quality", commands=["test"])
    ]
)
```

### Config Loading

```python
from sindri.config import load_config
from pathlib import Path

config = load_config(
    config_path=Path("sindri.toml"),
    start_path=Path.cwd()
)
```

## Groups API

### Command Group

```python
from sindri.core.group import CommandGroup

class MyGroup(CommandGroup):
    @property
    def id(self) -> str:
        return "mygroup"
    
    @property
    def title(self) -> str:
        return "My Group"
    
    def _create_commands(self) -> list:
        return [
            ShellCommand(
                id="my-command",
                shell="echo hello",
                title="My Command",
                group_id=self.id
            )
        ]
```

### Group Registration

```python
from sindri.core import get_registry, reset_registry

reset_registry()
registry = get_registry()
registry.discover_builtin_groups()
```

## CLI API

### Custom Commands

```python
from sindri.cli import app
import typer

@app.command("my-command")
def my_command():
    """My custom command."""
    typer.echo("Hello!")
```

### Command Parsing

```python
from sindri.cli.parsing import parse_command_parts

commands = parse_command_parts(config, ["docker", "build"])
```

## Utilities

### Shell Helpers

```python
from sindri.utils.helper import get_shell, escape_shell_arg

shell = get_shell()  # Returns shell path
escaped = escape_shell_arg("arg with spaces")
```

### Project Discovery

```python
from sindri.utils.helper import find_project_root

root = find_project_root(Path.cwd())
```

## Examples

### Custom Command Group

```python
from sindri.core.group import CommandGroup
from sindri.core.command import ShellCommand

class CustomGroup(CommandGroup):
    @property
    def id(self) -> str:
        return "custom"
    
    @property
    def title(self) -> str:
        return "Custom Commands"
    
    def _create_commands(self) -> list:
        return [
            ShellCommand(
                id="custom-command",
                shell="echo custom",
                title="Custom Command",
                group_id=self.id
            )
        ]
```

### Plugin Entry Point

```python
# pyproject.toml
[project.entry-points."sindri.groups"]
mygroup = "mypackage.groups:MyGroup"
```

---

**Hinweis:** Diese API ist noch in Entwicklung und kann sich ändern.

