# Recipes

Praktische Beispiele für verschiedene Use Cases und Workflows.

## Python Project

Vollständige Konfiguration für ein Python-Projekt mit Tests, Linting und Deployment.

```toml
version = "1.0"
project_name = "my-python-project"

# Reference built-in groups
groups = ["quality", "git", "pypi"]

[[commands]]
id = "setup"
title = "Setup Virtual Environment"
description = "Create venv and install dependencies"
shell = "python -m venv venv && . venv/bin/activate && pip install -r requirements.txt"
tags = ["setup"]

[[commands]]
id = "dev"
title = "Run Development Server"
description = "Start development server with auto-reload"
shell = "python -m app --reload"
watch = true
env = { DEBUG = "1", ENV = "development" }

[[commands]]
id = "deploy"
title = "Deploy to Production"
description = "Full deployment workflow"
shell = "deploy.sh"
dependencies = { before = ["test", "build"] }
timeout = 600
```

**Verwendung:**
```bash
# Setup
sindri run setup

# Development
sindri run dev  # Läuft kontinuierlich (Watch Mode)

# Quality Checks
sindri q check  # Alle Quality Checks

# Deploy
sindri run deploy  # Führt test und build vorher aus
```

## Docker Workflow

Vollständiger Docker-Workflow mit Build, Test und Push.

```toml
version = "1.0"
project_name = "my-docker-app"

groups = ["docker", "compose"]

[[commands]]
id = "docker-build"
title = "Build Docker Image"
shell = "docker build -t myapp:latest ."
tags = ["docker", "build"]

[[commands]]
id = "docker-test"
title = "Test Docker Image"
shell = "docker run --rm myapp:latest pytest"
tags = ["docker", "test"]
dependencies = { before = ["docker-build"] }

[[commands]]
id = "docker-push"
title = "Push to Registry"
shell = "docker push myapp:latest"
tags = ["docker", "push"]
dependencies = { before = ["docker-test"] }
```

**Verwendung:**
```bash
# Build
sindri d build

# Test
sindri run docker-test

# Push (führt build und test automatisch vorher aus)
sindri run docker-push
```

## Docker Compose Workflow

Docker Compose mit verschiedenen Profilen.

```toml
version = "1.0"
project_name = "my-compose-app"

groups = ["compose"]

[[commands]]
id = "compose-up"
title = "Start Services"
shell = "docker compose up -d"
tags = ["compose", "start"]

[[commands]]
id = "compose-down"
title = "Stop Services"
shell = "docker compose down"
tags = ["compose", "stop"]

[[commands]]
id = "compose-logs"
title = "View Logs"
shell = "docker compose logs -f"
tags = ["compose", "logs"]
watch = true

[[commands]]
id = "compose-restart"
title = "Restart Services"
shell = "docker compose restart"
tags = ["compose", "restart"]
dependencies = { before = ["compose-down"] }
```

**Verwendung:**
```bash
# Start
sindri c up

# Logs (Watch Mode)
sindri c logs

# Restart
sindri run compose-restart
```

## Node.js Project

Vollständige Node.js-Konfiguration mit npm/yarn.

```toml
version = "1.0"
project_name = "my-node-app"

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
watch = true
env = { NODE_ENV = "development" }

[[commands]]
id = "build"
title = "Build for Production"
shell = "npm run build"
tags = ["build"]
env = { NODE_ENV = "production" }

[[commands]]
id = "test"
title = "Run Tests"
shell = "npm test"
tags = ["test"]

[[commands]]
id = "lint"
title = "Lint Code"
shell = "npm run lint"
tags = ["lint", "quality"]
```

## Quality Assurance Workflow

Umfassendes Quality-Workflow mit allen Checks.

```toml
version = "1.0"
project_name = "my-project"

groups = ["quality"]

[[commands]]
id = "quality-check"
title = "Run All Quality Checks"
description = "Lint, format check, type check, and tests"
shell = "echo 'Running all quality checks...'"
dependencies = { before = ["lint", "format-check", "typecheck", "test"] }

[[commands]]
id = "lint"
title = "Lint Code"
shell = "ruff check ."
tags = ["quality", "lint"]

[[commands]]
id = "format-check"
title = "Check Formatting"
shell = "ruff format --check ."
tags = ["quality", "format"]

[[commands]]
id = "typecheck"
title = "Type Check"
shell = "mypy ."
tags = ["quality", "typecheck"]

[[commands]]
id = "test"
title = "Run Tests"
shell = "pytest tests/"
tags = ["quality", "test"]
```

**Verwendung:**
```bash
# Einzelne Checks
sindri q lint
sindri q format
sindri q typecheck
sindri q test

# Alle Checks
sindri q check

# Oder mit Custom Command
sindri run quality-check
```

## Git Workflow

Vollständiger Git-Workflow mit Built-in Commands.

```toml
version = "1.0"
project_name = "my-project"

groups = ["git"]

# Built-in Git Commands sind bereits verfügbar:
# - git-status
# - git-add
# - git-commit
# - git-push
# - git-pull
# - git-log
# - git-monitor
# - git-wf (workflow: add, commit, push, optional monitor)
```

**Verwendung:**
```bash
# Status
sindri g status

# Add, Commit, Push
sindri g wf

# Mit GitHub Actions Monitoring
sindri g wf --monitor

# Kontinuierliches Monitoring
sindri g monitor
```

## Multi-Environment Deployment

Deployment für verschiedene Umgebungen.

```toml
version = "1.0"
project_name = "my-app"

[[commands]]
id = "deploy-dev"
title = "Deploy to Development"
shell = "deploy.sh dev"
env = { ENV = "development", DEBUG = "1" }
dependencies = { before = ["test"] }

[[commands]]
id = "deploy-staging"
title = "Deploy to Staging"
shell = "deploy.sh staging"
env = { ENV = "staging", DEBUG = "0" }
dependencies = { before = ["test", "build"] }

[[commands]]
id = "deploy-prod"
title = "Deploy to Production"
shell = "deploy.sh production"
env = { ENV = "production", DEBUG = "0" }
dependencies = { before = ["test", "build"] }
timeout = 600
retries = 2
```

## CI/CD Pipeline Simulation

Simuliere eine CI/CD-Pipeline lokal.

```toml
version = "1.0"
project_name = "my-ci-project"

groups = ["quality"]

[[commands]]
id = "ci"
title = "Run CI Pipeline"
description = "Full CI pipeline: lint, test, build"
shell = "echo 'CI Pipeline completed'"
dependencies = { before = ["lint", "test", "build"] }

[[commands]]
id = "lint"
title = "Lint"
shell = "ruff check ."
tags = ["ci"]

[[commands]]
id = "test"
title = "Test"
shell = "pytest tests/ --cov"
tags = ["ci"]

[[commands]]
id = "build"
title = "Build"
shell = "python -m build"
tags = ["ci"]
```

**Verwendung:**
```bash
# Komplette CI-Pipeline
sindri run ci

# Oder parallel
sindri run lint test build --parallel
```

## Documentation Workflow

Dokumentations-Workflow mit MkDocs.

```toml
version = "1.0"
project_name = "my-docs-project"

groups = ["sindri"]

# Built-in Docs Commands:
# - docs-setup: Install dependencies
# - docs-preview: Start preview server
# - docs-build: Build documentation
# - docs-build-strict: Build with strict mode
# - docs-deploy: Deploy to GitHub Pages
```

**Verwendung:**
```bash
# Setup
sindri sindri docs-setup

# Preview (Watch Mode)
sindri sindri docs-preview

# Build
sindri sindri docs-build

# Deploy
sindri sindri docs-deploy
```

## PyPI Publishing Workflow

Vollständiger PyPI-Publishing-Workflow.

```toml
version = "1.0"
project_name = "my-package"

groups = ["pypi", "quality"]

[[commands]]
id = "publish"
title = "Publish to PyPI"
description = "Full publishing workflow"
shell = "echo 'Publishing to PyPI...'"
dependencies = { before = ["test", "pypi-push"] }

[[commands]]
id = "pypi-push"
title = "Build and Push Package"
shell = "python -m build && python -m twine upload dist/*"
tags = ["pypi", "build", "push"]
dependencies = { before = ["test"] }
```

**Verwendung:**
```bash
# Build
sindri p build

# Upload
sindri p upload

# Oder kompletter Workflow
sindri run publish
```

## Watch Mode Examples

Commands, die kontinuierlich laufen.

```toml
version = "1.0"
project_name = "my-watch-project"

[[commands]]
id = "dev-server"
title = "Development Server"
shell = "python -m app --reload"
watch = true
env = { DEBUG = "1" }

[[commands]]
id = "tail-logs"
title = "Tail Logs"
shell = "tail -f logs/app.log"
watch = true

[[commands]]
id = "watch-tests"
title = "Watch Tests"
shell = "pytest-watch tests/"
watch = true
```

**Hinweis:** Watch-Mode Commands laufen kontinuierlich. Beende sie mit `Ctrl+C`.

## Parallel Execution Examples

Mehrere Commands parallel ausführen.

```toml
version = "1.0"
project_name = "my-parallel-project"

[[commands]]
id = "build-frontend"
title = "Build Frontend"
shell = "npm run build"
cwd = "frontend"
tags = ["build"]

[[commands]]
id = "build-backend"
title = "Build Backend"
shell = "python -m build"
cwd = "backend"
tags = ["build"]

[[commands]]
id = "build-all"
title = "Build All"
description = "Build frontend and backend in parallel"
shell = "echo 'Building all...'"
dependencies = { before = ["build-frontend", "build-backend"] }
```

**Verwendung:**
```bash
# Parallel ausführen
sindri run build-frontend build-backend --parallel

# Oder mit Dependencies
sindri run build-all
```

## Best Practices

### 1. Verwende Built-in Groups

Nutze die vordefinierten Groups, wenn möglich:

```toml
groups = ["quality", "docker", "git"]
```

### 2. Definiere klare Dependencies

```toml
[[commands]]
id = "deploy"
dependencies = { before = ["test", "build"] }
```

### 3. Setze realistische Timeouts

```toml
[[commands]]
id = "long-task"
timeout = 600  # 10 Minuten
```

### 4. Nutze Tags für Organisation

```toml
[[commands]]
id = "test"
tags = ["test", "quality", "ci"]
```

### 5. Verwende Watch Mode für Development

```toml
[[commands]]
id = "dev"
watch = true
env = { DEBUG = "1" }
```
