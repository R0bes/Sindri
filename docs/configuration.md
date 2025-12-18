# Konfiguration

Sindri verwendet TOML-Konfigurationsdateien. Die Config-Datei wird automatisch durch Suche nach oben vom aktuellen Arbeitsverzeichnis nach `sindri.toml` oder `.sindri.toml` gefunden.

## Grundlegende Konfiguration

```toml
version = "1.0"
project_name = "my-project"

[[commands]]
id = "setup"
title = "Setup Project"
description = "Install dependencies"
shell = "pip install -r requirements.txt"
tags = ["setup", "install"]
```

## Command-Definitionen

### Basis-Properties

Jeder Command benötigt folgende Properties:

- **id** (erforderlich): Eindeutige Command-ID, wird für die Ausführung verwendet
- **shell** (erforderlich): Shell-Command zum Ausführen
- **title** (optional): Anzeigename, verwendet `id` als Fallback
- **description** (optional): Beschreibung des Commands
- **tags** (optional): Tags für Kategorisierung und Filterung

### Erweiterte Features

#### Command Dependencies

Definiere Abhängigkeiten zwischen Commands. Commands können vor oder nach anderen Commands ausgeführt werden.

```toml
[[commands]]
id = "restart"
title = "Restart Service"
shell = "pkill -f app && sleep 1 && python -m app"
dependencies = { before = ["stop"] }

[[commands]]
id = "deploy"
title = "Deploy Application"
shell = "deploy.sh"
dependencies = { before = ["test", "build"], after = ["notify"] }
```

**Verfügbare Optionen:**
- `before`: Liste von Commands, die vor diesem Command ausgeführt werden
- `after`: Liste von Commands, die nach diesem Command ausgeführt werden

#### Watch Mode

Commands können im Watch-Mode ausgeführt werden, um kontinuierlich zu laufen.

```toml
[[commands]]
id = "tail-logs"
title = "Tail Logs"
shell = "tail -f logs/app.log"
watch = true

[[commands]]
id = "dev-server"
title = "Development Server"
shell = "python -m app --reload"
watch = true
```

**Hinweis:** Watch-Mode Commands laufen kontinuierlich und können mit `Ctrl+C` beendet werden.

#### Environment Variables

Setze Environment-Variablen für Commands.

```toml
[[commands]]
id = "run-dev"
title = "Run in Development Mode"
shell = "python -m app"
env = { DEBUG = "1", ENV = "development", PORT = "8000" }

[[commands]]
id = "run-prod"
title = "Run in Production Mode"
shell = "python -m app"
env = { DEBUG = "0", ENV = "production", PORT = "80" }
```

#### Timeouts und Retries

Definiere Timeouts und Retry-Logik für Commands.

```toml
[[commands]]
id = "long-task"
title = "Long Running Task"
shell = "python long_task.py"
timeout = 300  # 5 Minuten in Sekunden
retries = 3    # Anzahl der Wiederholungen bei Fehler

[[commands]]
id = "network-request"
title = "Network Request"
shell = "curl https://api.example.com/data"
timeout = 30
retries = 5
```

**Hinweise:**
- Timeout wird in Sekunden angegeben
- Bei Timeout wird der Command beendet (Exit Code 124 auf Unix, 1 auf Windows)
- Retries werden nur bei Fehlern (Exit Code != 0) ausgeführt

#### Working Directory

Setze ein spezifisches Arbeitsverzeichnis für Commands.

```toml
[[commands]]
id = "build-frontend"
title = "Build Frontend"
shell = "npm run build"
cwd = "frontend"  # Relativ zum Projekt-Root

[[commands]]
id = "build-backend"
title = "Build Backend"
shell = "python -m build"
cwd = "backend"
```

## Command Groups

Gruppiere verwandte Commands für bessere Organisation.

```toml
[[groups]]
id = "setup"
title = "Setup"
description = "Setup and installation commands"
order = 1
commands = ["setup", "install", "update"]

[[groups]]
id = "development"
title = "Development"
description = "Development workflow commands"
order = 2
commands = ["dev", "test", "lint"]
```

**Properties:**
- **id**: Eindeutige Gruppen-ID
- **title**: Anzeigename der Gruppe
- **description**: Beschreibung der Gruppe
- **order**: Sortierreihenfolge (niedrigere Zahlen zuerst)
- **commands**: Liste von Command-IDs, die zu dieser Gruppe gehören

## Built-in Command Groups

Sindri bietet mehrere vordefinierte Command-Gruppen, die in der `sindri.toml` referenziert werden können:

```toml
version = "1.0"

# Reference implemented command groups
groups = [
    "sindri",      # Sindri-spezifische Commands (docs-setup, docs-preview, etc.)
    "general",     # Allgemeine Commands
    "quality",     # Quality-Commands (lint, format, test, test-cov, check)
    "application", # Application-Commands (start, stop, restart)
    "docker",      # Docker-Commands (build, run, push)
    "compose",     # Docker Compose-Commands (up, down, logs)
    "git",         # Git-Commands (status, add, commit, push, pull, log, monitor, wf)
    "pypi",        # PyPI-Publishing (build, upload)
]
```

### Verfügbare Built-in Groups

| Group | Commands | Beschreibung |
|-------|----------|--------------|
| `sindri` | `docs-setup`, `docs-preview`, `docs-build`, `docs-build-strict`, `docs-deploy` | Sindri-spezifische Commands für Dokumentation |
| `general` | `setup`, `install`, etc. | Allgemeine Commands |
| `quality` | `lint`, `format`, `typecheck`, `test`, `test-cov`, `check` | Code-Qualität, Linting, Formatting, Tests |
| `application` | `app-run`, `app-dev` | Application Lifecycle Management |
| `docker` | `docker-build`, `docker-push`, `docker-build_and_push`, `docker-up`, `docker-down`, `docker-restart`, `docker-logs`, `docker-logs-tail` | Docker Container und Image Operations |
| `compose` | `compose-up`, `compose-down`, `compose-restart`, `compose-build`, `compose-logs`, `compose-logs-tail`, `compose-ps`, `compose-pull` | Docker Compose Service Management |
| `git` | `git-status`, `git-add`, `git-commit`, `git-push`, `git-pull`, `git-log`, `git-monitor`, `git-wf` | Git Version Control Operations |
| `version` | `version show`, `version bump`, `version tag` | Version Management |
| `pypi` | `pypi-validate`, `pypi-push` | PyPI Publishing Operations |
| `general` | `setup-venv`, `setup-install` | General setup commands |
| `sindri` | `docs-setup`, `docs-preview`, `docs-build`, `docs-build-strict`, `docs-deploy` | Sindri-spezifische Commands |

## Config-Discovery

Sindri sucht nach Config-Dateien in folgender Reihenfolge:

1. `.sindri/sindri.toml` (im Projekt-Root)
2. `sindri.toml` (im Projekt-Root)
3. `pyproject.toml` (unter `[tool.sindri]`)

Die Suche beginnt im aktuellen Verzeichnis und geht nach oben bis zum Projekt-Root (erkennbar an `.git`, `pyproject.toml`, etc.).

### Beispiel: pyproject.toml Integration

```toml
[tool.sindri]
version = "1.0"
project_name = "my-project"

[[tool.sindri.commands]]
id = "test"
title = "Run Tests"
shell = "pytest tests/"

[[tool.sindri.commands]]
id = "lint"
title = "Lint Code"
shell = "ruff check ."
```

## Erweiterte Konfiguration

### Globale Einstellungen

```toml
version = "1.0"
project_name = "my-project"

# Globale Timeout-Einstellung (kann pro Command überschrieben werden)
default_timeout = 60

# Globale Retry-Einstellung
default_retries = 2
```

### Command-Templates

Verwende Template-Variablen in Commands:

```toml
[[commands]]
id = "deploy"
title = "Deploy to Environment"
shell = "deploy.sh {{ env }}"
# env wird zur Laufzeit ersetzt
```

**Verfügbare Template-Variablen:**
- `{{ project_name }}`: Projektname aus Config
- `{{ cwd }}`: Aktuelles Arbeitsverzeichnis
- Custom-Variablen können über Environment-Variablen gesetzt werden

## Best Practices

### 1. Sinnvolle Command-IDs

Verwende klare, beschreibende IDs:

```toml
# ✅ Gut
id = "test-with-coverage"
id = "docker-build-prod"

# ❌ Schlecht
id = "cmd1"
id = "do-stuff"
```

### 2. Tags für Organisation

Nutze Tags für bessere Filterung und Organisation:

```toml
[[commands]]
id = "test"
tags = ["test", "quality", "ci"]

[[commands]]
id = "test-integration"
tags = ["test", "integration", "ci"]
```

### 3. Dependencies richtig verwenden

Definiere klare Abhängigkeiten:

```toml
[[commands]]
id = "deploy"
dependencies = { before = ["test", "build"] }
```

### 4. Timeouts für lange Commands

Setze realistische Timeouts:

```toml
[[commands]]
id = "long-build"
timeout = 600  # 10 Minuten für Builds
```

## Beispiele

Siehe [Recipes](recipes.md) für vollständige Beispiel-Konfigurationen für verschiedene Use Cases.

## Troubleshooting

### Config wird nicht gefunden

- Stelle sicher, dass `sindri.toml` im Projekt-Root liegt
- Prüfe, ob das Projekt-Root korrekt erkannt wird (`.git`, `pyproject.toml`, etc.)
- Verwende `--config` um explizit eine Config-Datei anzugeben

### Commands werden nicht gefunden

- Prüfe, ob die Command-IDs korrekt geschrieben sind
- Stelle sicher, dass Built-in Groups in `groups = [...]` referenziert sind
- Verwende `sindri list` um alle verfügbaren Commands zu sehen

### Dependencies funktionieren nicht

- Stelle sicher, dass abhängige Commands existieren
- Prüfe auf zirkuläre Abhängigkeiten
- Commands in `before` werden vor dem Command ausgeführt
- Commands in `after` werden nach dem Command ausgeführt
