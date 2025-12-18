<div align="center">

![Sindri Logo](assets/logo.png)

# Sindri

A project-configurable command palette for common dev workflows. Sindri provides an interactive TUI (Text User Interface) and CLI for managing project-specific commands, making it easy to run setup, build, test, and deployment tasks.

</div>

## Features

- 🎯 **Interactive TUI**: Beautiful terminal interface with search, filtering, and command details
- 📝 **Project-Specific Config**: Each repository defines its own commands via `sindri.toml`
- 🚀 **Async Execution**: Run commands asynchronously with live output streaming
- 🔄 **Parallel Execution**: Run multiple commands concurrently
- 📊 **Multi-Stream Logs**: View logs from multiple commands in split panes
- ⚙️ **Rich Configuration**: Support for dependencies, timeouts, retries, watch mode, and more
- 🐳 **Docker Support**: Built-in support for Docker and Docker Compose workflows
- 📦 **Easy Installation**: Install via `pip install sindri-dev`, use in any project

## Quickstart

### Installation

```bash
pip install sindri-dev
```

Or install with optional extras:

```bash
pip install sindri-dev[docker,compose,git,version,pypi]
```

Or install from source:

```bash
git clone https://github.com/R0bes/Sindri.git
cd sindri
pip install -e .
```

### Initialize a Project

Navigate to your project directory and run:

```bash
sindri init
```

This creates a `sindri.toml` file with example commands. Edit it to match your project's needs.

### Use Sindri

Open the interactive menu:

```bash
sindri
```

Or run commands directly:

```bash
sindri run setup
sindri run start --parallel
```

## Configuration

Sindri uses TOML configuration files. The config file is discovered by searching upwards from the current working directory for `sindri.toml` or `.sindri.toml`.

### Basic Configuration

```toml
version = "1.0"
project_name = "my-project"

[[commands]]
id = "setup"
title = "Setup Project"
description = "Install dependencies"
shell = "pip install -r requirements.txt"
tags = ["setup", "install"]

[[commands]]
id = "start"
title = "Start Service"
description = "Start the application"
shell = "python -m myproject.main"
tags = ["run", "start"]
```

### Advanced Features

#### Command Dependencies

```toml
[[commands]]
id = "restart"
title = "Restart Service"
shell = "pkill -f app && sleep 1 && python -m app"
dependencies = { before = ["stop"] }
```

#### Watch Mode

```toml
[[commands]]
id = "tail-logs"
title = "Tail Logs"
shell = "tail -f logs/app.log"
watch = true
```

#### Environment Variables

```toml
[[commands]]
id = "run-dev"
title = "Run in Development Mode"
shell = "python -m app"
env = { DEBUG = "1", ENV = "development" }
```

#### Timeouts and Retries

```toml
[[commands]]
id = "long-task"
title = "Long Running Task"
shell = "python long_task.py"
timeout = 300  # 5 minutes
retries = 3
```

#### Command Groups

```toml
[[groups]]
id = "setup"
title = "Setup"
description = "Setup commands"
order = 1
commands = ["setup", "install"]
```

#### Docker Compose Profiles

```toml
[[compose_profiles]]
id = "dev"
title = "Development Profile"
profiles = ["dev"]
command = "up"
flags = ["-d"]
```

See [examples/example-project/sindri.toml](examples/example-project/sindri.toml) for a complete example.

## CLI Commands

### `sindri init`

Initialize a new Sindri configuration file in the current directory.

```bash
sindri init
sindri init --config custom.toml
```

### `sindri run <command-id>`

Run one or more commands non-interactively.

```bash
sindri run setup
sindri run start web api --parallel
sindri run test --timeout 60 --retries 2
```

**Options:**
- `--config, -c`: Path to config file
- `--dry-run`: Show what would be executed without running
- `--verbose, -v`: Enable verbose logging
- `--json-logs`: Output logs in JSON format
- `--timeout, -t`: Timeout in seconds
- `--retries, -r`: Number of retries on failure
- `--parallel, -p`: Run multiple commands in parallel

### `sindri list`

List all available commands.

```bash
sindri list
```

### `sindri` (default)

Open the interactive TUI menu.

```bash
sindri
sindri --config custom.toml
```

**Options:**
- `--config, -c`: Path to config file
- `--verbose, -v`: Enable verbose logging
- `--json-logs`: Output logs in JSON format

## TUI Navigation

The interactive TUI provides the following keybindings:

- `Ctrl+F` or `/`: Focus search input
- `Enter`: Run selected command
- `↑/↓`: Navigate command list
- `Tab`: Switch between panels
- `Ctrl+C` or `Q`: Quit

## Recipes

### Docker Workflow

```toml
[[commands]]
id = "docker-build"
title = "Build Docker Image"
shell = "docker build -t myapp:latest ."
tags = ["docker", "build"]

[[commands]]
id = "docker-run"
title = "Run Docker Container"
shell = "docker run -p 8000:8000 myapp:latest"
tags = ["docker", "run"]
```

### Docker Compose Workflow

```toml
[[commands]]
id = "compose-up"
title = "Start Services"
shell = "docker compose up -d"
tags = ["docker", "compose"]

[[commands]]
id = "compose-logs"
title = "View Logs"
shell = "docker compose logs -f"
tags = ["docker", "compose", "logs"]
watch = true
```

### Python Virtual Environment

```toml
[[commands]]
id = "setup"
title = "Setup Virtual Environment"
shell = "python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
tags = ["setup"]

[[commands]]
id = "activate"
title = "Activate Virtual Environment"
shell = "source venv/bin/activate"
tags = ["setup"]
```

### Node.js Project

```toml
[[commands]]
id = "install"
title = "Install Dependencies"
shell = "npm install"
tags = ["setup", "install"]

[[commands]]
id = "dev"
title = "Start Dev Server"
shell = "npm run dev"
tags = ["run", "dev"]

[[commands]]
id = "build"
title = "Build for Production"
shell = "npm run build"
tags = ["build"]
```

### Build Executable (PyInstaller)

```toml
[[commands]]
id = "build-exe"
title = "Build Executable"
shell = "pyinstaller --onefile --name myapp src/main.py"
tags = ["build", "executable"]
```

### Test Suite with Coverage

```toml
[[commands]]
id = "test"
title = "Run Tests"
shell = "pytest tests/"
tags = ["test"]

[[commands]]
id = "test-cov"
title = "Run Tests with Coverage"
shell = "pytest --cov=myproject --cov-report=html tests/"
tags = ["test", "coverage"]
```

## Screenshots

> **Note**: Screenshots will be added here once the TUI is finalized.

### Main Screen
![Main Screen](docs/screenshots/main-screen.png)

### Command Execution
![Command Execution](docs/screenshots/command-execution.png)

### Multi-Stream Logs
![Multi-Stream Logs](docs/screenshots/multi-stream-logs.png)

## Architecture

Sindri is built with:

- **Typer**: CLI framework
- **Textual**: TUI framework
- **Pydantic**: Configuration validation
- **asyncio**: Async command execution
- **structlog**: Structured logging

### Project Structure

```
sindri/
├── sindri/
│   ├── cli.py          # CLI interface
│   ├── config.py        # Config discovery and schema
│   ├── runner.py        # Async execution engine
│   ├── logging.py       # Structured logging
│   ├── utils.py         # Utility functions
│   └── tui/             # TUI components
│       ├── app.py       # Main TUI app
│       ├── screens.py   # TUI screens
│       └── widgets.py   # TUI widgets
├── tests/               # Test suite
├── examples/            # Example configurations
└── pyproject.toml       # Project configuration
```

## Development

### Setup

```bash
git clone https://github.com/R0bes/Sindri.git
cd sindri
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
pytest --cov=sindri
```

### Building

```bash
python -m build
```

### CI/CD

Das Projekt verwendet GitHub Actions für CI/CD:

- **CI**: Automatische Tests und Linting bei jedem Push/PR
- **Release**: Automatisches Build und Push zu PyPI bei Version-Tags
- **Auto Version Bump**: Automatisches Erstellen von Version-Tags bei Änderungen in `pyproject.toml`

Siehe [.github/workflows/README.md](.github/workflows/README.md) für Details.

## Platform Support

- ✅ **Linux**: Full support
- ✅ **macOS**: Full support
- ⚠️ **Windows**: Supported with some limitations:
  - Shell command syntax may differ (use `cmd.exe` syntax or PowerShell)
  - Some Unix commands may not be available
  - Path separators are handled automatically

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) for the TUI
- Uses [Typer](https://github.com/tiangolo/typer) for the CLI
- Configuration powered by [Pydantic](https://github.com/pydantic/pydantic)

