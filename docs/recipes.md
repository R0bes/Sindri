# Recipes

Praktische Beispiele für verschiedene Use Cases.

## Docker Workflow

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

[[commands]]
id = "docker-push"
title = "Push to Registry"
shell = "docker push myapp:latest"
tags = ["docker", "push"]
```

## Docker Compose Workflow

```toml
[[commands]]
id = "compose-up"
title = "Start Services"
shell = "docker compose up -d"
tags = ["docker", "compose"]

[[commands]]
id = "compose-down"
title = "Stop Services"
shell = "docker compose down"
tags = ["docker", "compose"]

[[commands]]
id = "compose-logs"
title = "View Logs"
shell = "docker compose logs -f"
tags = ["docker", "compose", "logs"]
watch = true
```

## Python Virtual Environment

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

[[commands]]
id = "test"
title = "Run Tests"
shell = "source venv/bin/activate && pytest tests/"
tags = ["test"]
```

## Node.js Project

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
watch = true

[[commands]]
id = "build"
title = "Build for Production"
shell = "npm run build"
tags = ["build"]
```

## Test Suite with Coverage

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

[[commands]]
id = "test-watch"
title = "Run Tests in Watch Mode"
shell = "pytest-watch tests/"
tags = ["test"]
watch = true
```

## Build Executable (PyInstaller)

```toml
[[commands]]
id = "build-exe"
title = "Build Executable"
shell = "pyinstaller --onefile --name myapp src/main.py"
tags = ["build", "executable"]

[[commands]]
id = "clean-build"
title = "Clean Build Artifacts"
shell = "rm -rf build dist *.spec"
tags = ["clean"]
```

## Multi-Command Workflows

```toml
[[commands]]
id = "deploy"
title = "Deploy Application"
shell = "echo 'Deploying...'"
dependencies = { before = ["test", "build"] }

[[commands]]
id = "test"
title = "Run Tests"
shell = "pytest tests/"

[[commands]]
id = "build"
title = "Build Application"
shell = "python -m build"
```

## Environment-Specific Commands

```toml
[[commands]]
id = "run-dev"
title = "Run in Development"
shell = "python -m app"
env = { DEBUG = "1", ENV = "development" }

[[commands]]
id = "run-prod"
title = "Run in Production"
shell = "python -m app"
env = { DEBUG = "0", ENV = "production" }
```

## Git Workflow

```toml
[[commands]]
id = "git-commit"
title = "Commit Changes"
shell = "git add . && git commit -m 'Update'"
tags = ["git"]

[[commands]]
id = "git-push"
title = "Push to Remote"
shell = "git push"
tags = ["git"]
dependencies = { before = ["git-commit"] }
```

## Version Management

```toml
[[commands]]
id = "version-bump-patch"
title = "Bump Patch Version"
shell = "echo 'Bumping patch version'"
tags = ["version"]

[[commands]]
id = "version-bump-minor"
title = "Bump Minor Version"
shell = "echo 'Bumping minor version'"
tags = ["version"]

[[commands]]
id = "version-bump-major"
title = "Bump Major Version"
shell = "echo 'Bumping major version'"
tags = ["version"]
```

