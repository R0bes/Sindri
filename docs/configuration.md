# Konfiguration

Sindri verwendet TOML-Konfigurationsdateien. Die Config-Datei wird automatisch durch Suche nach oben vom aktuellen Arbeitsverzeichnis nach `sindri.toml` oder `.sindri/sindri.toml` gefunden.

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

- **id**: Eindeutige Command-ID (erforderlich)
- **title**: Anzeigename (optional, verwendet id als Fallback)
- **description**: Beschreibung (optional)
- **shell**: Shell-Command zum Ausführen (erforderlich)
- **tags**: Tags für Kategorisierung (optional)

### Erweiterte Features

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

#### Timeouts und Retries

```toml
[[commands]]
id = "long-task"
title = "Long Running Task"
shell = "python long_task.py"
timeout = 300  # 5 Minuten
retries = 3
```

## Command Groups

Gruppieren Sie verwandte Commands:

```toml
[[groups]]
id = "setup"
title = "Setup"
description = "Setup commands"
order = 1
commands = ["setup", "install"]
```

## Docker Compose Profiles

```toml
[[compose_profiles]]
id = "dev"
title = "Development Profile"
profiles = ["dev"]
command = "up"
flags = ["-d"]
```

## Config-Discovery

Sindri sucht nach Config-Dateien in folgender Reihenfolge:

1. `.sindri/sindri.toml` (im Projekt-Root)
2. `sindri.toml` (im Projekt-Root)
3. `pyproject.toml` (unter `[tool.sindri]`)

Die Suche beginnt im aktuellen Verzeichnis und geht nach oben bis zum Projekt-Root.

## Built-in Command Groups

Sindri bietet mehrere vordefinierte Command-Gruppen:

- **quality**: Test- und Quality-Commands (pytest, coverage, lint)
- **docker**: Docker-Commands (build, run, push)
- **compose**: Docker Compose-Commands (up, down, logs)
- **git**: Git-Commands (commit, push, pull)
- **version**: Version-Management (bump, show)
- **pypi**: PyPI-Publishing (build, upload)
- **application**: Application-Commands (start, stop, restart)
- **general**: Allgemeine Commands

Diese können in der `sindri.toml` referenziert werden:

```toml
groups = ["quality", "docker", "git"]
```

## Erweiterte Konfiguration

Siehe [examples/](examples/) für vollständige Beispiel-Konfigurationen.

