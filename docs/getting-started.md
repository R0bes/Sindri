# Getting Started

Dieser Guide führt Sie durch die Installation und ersten Schritte mit Sindri.

## Installation

### Via pip

```bash
pip install sindri-dev
```

### Mit optionalen Extras

Installiere Sindri mit zusätzlichen Features für Docker, Git, Version Management und PyPI:

```bash
pip install sindri-dev[docker,compose,git,version,pypi]
```

### Von Source

Für Entwicklung oder die neueste Version:

```bash
git clone https://github.com/R0bes/Sindri.git
cd sindri
pip install -e ".[dev]"
```

## Projekt initialisieren

Navigieren Sie zu Ihrem Projektverzeichnis und führen Sie aus:

```bash
sindri init
```

Dies erstellt eine `sindri.toml` Datei mit Beispiel-Commands. Bearbeiten Sie diese, um sie an die Bedürfnisse Ihres Projekts anzupassen.

### Interaktiver Modus

Der interaktive Modus erkennt automatisch Ihren Projekttyp (Python, Node.js, Docker, etc.) und schlägt passende Command-Gruppen vor:

```bash
sindri init --interactive
```

**Erkannte Projekttypen:**
- Python (pyproject.toml, setup.py, requirements.txt)
- Node.js (package.json)
- Docker (Dockerfile, docker-compose.yml)
- Git (`.git` Verzeichnis)

### Non-Interactive Modus

Erstellt eine Standard-Konfiguration ohne Interaktion:

```bash
sindri init --no-interactive
```

### Custom Config-Datei

Erstelle eine Config-Datei mit einem benutzerdefinierten Namen:

```bash
sindri init --config custom.toml
```

## Erste Schritte

### 1. Interaktive TUI öffnen

Die einfachste Art, Sindri zu verwenden:

```bash
sindri
```

Die TUI bietet:
- 🔍 **Suchfunktion** für Commands (Strg+F oder `/`)
- 📋 **Übersichtliche Command-Liste** mit Gruppierung
- 📊 **Live-Logs** während der Ausführung
- ⌨️  **Tastatur-Navigation** (↑/↓, Enter, Tab)
- 🔄 **Multi-Stream Logs** für parallele Commands

**Tastenkürzel:**
- `Ctrl+F` oder `/`: Fokus auf Suchfeld
- `Enter`: Ausgewählten Command ausführen
- `↑/↓`: Durch Command-Liste navigieren
- `Tab`: Zwischen Panels wechseln
- `Ctrl+C` oder `Q`: Beenden

### 2. Commands direkt ausführen

Für Scripts und CI/CD:

```bash
# Einzelner Command
sindri run setup

# Mehrere Commands nacheinander
sindri run test build

# Mehrere Commands parallel
sindri run start web api --parallel

# Mit Optionen
sindri run test --timeout 60 --retries 2
```

### 3. Built-in Commands verwenden

Sindri bietet vordefinierte Command-Gruppen:

```bash
# Quality Commands
sindri q test          # Tests ausführen
sindri q test-cov      # Tests mit Coverage
sindri q lint          # Linting
sindri q format        # Code formatieren
sindri q check         # Alle Quality Checks

# Docker Commands
sindri d build         # Docker Build
sindri d run           # Docker Run

# Git Commands
sindri g status        # Git Status
sindri g wf            # Workflow: add, commit, push
sindri g wf --monitor  # Mit GitHub Actions Monitoring

# Version Management
sindri version show
sindri version bump --patch
```

### 4. Command-Liste anzeigen

Zeige alle verfügbaren Commands:

```bash
sindri list
```

## Beispiel-Konfiguration

Eine minimale `sindri.toml` könnte so aussehen:

```toml
version = "1.0"
project_name = "my-project"

[[commands]]
id = "setup"
title = "Setup Project"
description = "Install dependencies"
shell = "pip install -r requirements.txt"
tags = ["setup"]

[[commands]]
id = "test"
title = "Run Tests"
description = "Execute test suite"
shell = "pytest tests/"
tags = ["test"]
```

### Mit Built-in Groups

Nutze vordefinierte Command-Gruppen:

```toml
version = "1.0"
project_name = "my-project"

# Reference built-in groups
groups = ["quality", "docker", "git"]

# Zusätzliche Custom Commands
[[commands]]
id = "setup"
title = "Setup Project"
shell = "pip install -r requirements.txt"
```

### Mit erweiterten Features

```toml
version = "1.0"
project_name = "my-project"

groups = ["quality"]

[[commands]]
id = "dev"
title = "Development Server"
shell = "python -m app --reload"
watch = true  # Läuft kontinuierlich
env = { DEBUG = "1", ENV = "development" }

[[commands]]
id = "deploy"
title = "Deploy"
shell = "deploy.sh"
dependencies = { before = ["test", "build"] }  # Führt test und build vorher aus
timeout = 600  # 10 Minuten
retries = 2
```

## Häufige Workflows

### Python-Projekt Setup

```bash
# 1. Projekt initialisieren
sindri init --interactive

# 2. Setup ausführen
sindri run setup

# 3. Tests ausführen
sindri q test

# 4. Development Server starten
sindri run dev  # Falls watch=true gesetzt
```

### Git Workflow

```bash
# Kompletter Workflow: add, commit, push
sindri g wf

# Mit GitHub Actions Monitoring
sindri g wf --monitor
```

### Quality Checks

```bash
# Alle Quality Checks
sindri q check

# Oder einzeln
sindri q lint
sindri q format
sindri q typecheck
sindri q test-cov
```

### Docker Workflow

```bash
# Build
sindri d build

# Run
sindri d run

# Compose
sindri c up
sindri c logs
```

## Nächste Schritte

### Für Benutzer

- 📖 [Konfiguration](configuration.md) - Detaillierte Konfigurationsoptionen
- 📋 [CLI Referenz](cli-reference.md) - Alle CLI-Befehle im Detail
- 🍳 [Recipes](recipes.md) - Praktische Beispiele für verschiedene Use Cases

### Für Entwickler

- 🏗️ [Architektur](architecture.md) - Systemarchitektur und Design-Entscheidungen
- 💻 [Development Guide](development.md) - Setup und Entwicklungsumgebung
- 🧪 [Testing](testing.md) - Test-Strategie und Coverage
- 📚 [API Referenz](api-reference.md) - API-Dokumentation

## Troubleshooting

### Config wird nicht gefunden

- Stelle sicher, dass `sindri.toml` im Projekt-Root liegt
- Prüfe, ob das Projekt-Root korrekt erkannt wird (`.git`, `pyproject.toml`, etc.)
- Verwende `--config` um explizit eine Config-Datei anzugeben

### Commands werden nicht gefunden

- Prüfe, ob die Command-IDs korrekt geschrieben sind
- Stelle sicher, dass Built-in Groups in `groups = [...]` referenziert sind
- Verwende `sindri list` um alle verfügbaren Commands zu sehen

### Built-in Commands funktionieren nicht

- Stelle sicher, dass die entsprechenden Tools installiert sind (ruff, mypy, pytest, docker, etc.)
- Built-in Commands verwenden `python -m` für Python-Tools
- Prüfe, ob die Tools im PATH verfügbar sind

## Hilfe erhalten

- 📖 Dokumentation: Diese Docs
- 🐛 Issues: [GitHub Issues](https://github.com/R0bes/Sindri/issues)
- 💬 Diskussionen: [GitHub Discussions](https://github.com/R0bes/Sindri/discussions)
