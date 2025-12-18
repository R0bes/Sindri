# CLI Referenz

Vollständige Referenz aller CLI-Befehle und Optionen.

## Grundlegende Commands

### `sindri init`

Initialisiert eine neue Sindri-Konfigurationsdatei im aktuellen Verzeichnis.

```bash
sindri init
sindri init --config custom.toml
sindri init --interactive
sindri init --no-interactive
```

**Optionen:**
- `--config, -c`: Pfad zur Config-Datei
- `--interactive/--no-interactive`: Interaktiven Modus verwenden

### `sindri run <command-id>`

Führt einen oder mehrere Commands nicht-interaktiv aus.

```bash
# Einzelner Command
sindri run setup

# Mehrere Commands
sindri run start web api

# Parallel ausführen
sindri run start web api --parallel

# Mit Optionen
sindri run test --timeout 60 --retries 2
```

**Optionen:**
- `--config, -c`: Pfad zur Config-Datei
- `--dry-run`: Zeigt was ausgeführt würde, ohne es auszuführen
- `--verbose, -v`: Aktiviert verbose Logging
- `--json-logs`: Gibt Logs im JSON-Format aus
- `--timeout, -t`: Timeout in Sekunden
- `--retries, -r`: Anzahl der Wiederholungen bei Fehler
- `--parallel, -p`: Führt mehrere Commands parallel aus

### `sindri list`

Listet alle verfügbaren Commands auf.

```bash
sindri list
sindri list --config custom.toml
```

**Optionen:**
- `--config, -c`: Pfad zur Config-Datei

### `sindri` (Standard)

Öffnet die interaktive TUI.

```bash
sindri
sindri --config custom.toml
```

**Optionen:**
- `--config, -c`: Pfad zur Config-Datei
- `--verbose, -v`: Aktiviert verbose Logging
- `--json-logs`: Gibt Logs im JSON-Format aus

## Namespace Commands

Sindri unterstützt Namespace-Commands für Built-in-Gruppen. Diese können über Kurzformen (Aliases) oder vollständige Namen aufgerufen werden.

### Quality Commands (`q` / `quality`)

Code-Qualität, Linting, Formatting und Tests.

```bash
# Linting
sindri q lint
sindri quality lint

# Formatting
sindri q format
sindri quality format

# Type Checking
sindri q typecheck
sindri quality typecheck

# Tests
sindri q test
sindri quality test

# Tests mit Coverage
sindri q test-cov
sindri quality test-cov

# Alle Quality Checks
sindri q check
sindri quality check
```

**Verfügbare Commands:**
- `lint` - Run ruff linter
- `format` - Format code with ruff
- `typecheck` - Run mypy type checker
- `test` - Run pytest test suite
- `test-cov` - Run tests with coverage report
- `check` - Run all quality checks (lint, format check, typecheck)

### Docker Commands (`d` / `docker`)

Docker Container und Image Operations.

```bash
# Build
sindri d build
sindri docker build

# Push
sindri d push
sindri docker push

# Build & Push (Alias: bp)
sindri d bp
sindri docker build_and_push

# Container Management
sindri d up
sindri docker up

sindri d down
sindri docker down

sindri d restart
sindri docker restart

# Logs
sindri d logs
sindri docker logs

sindri d logs-tail
sindri docker logs-tail
```

**Verfügbare Commands:**
- `docker-build` - Build Docker image with latest and version tags
- `docker-push` - Push Docker image to registry
- `docker-build_and_push` - Build and push in sequence (Alias: `bp`)
- `docker-up` - Start Docker container
- `docker-down` - Stop Docker container
- `docker-restart` - Restart Docker container
- `docker-logs` - Follow Docker container logs (Watch Mode)
- `docker-logs-tail` - Show last 100 lines of logs

### Docker Compose Commands (`c` / `compose` / `dc`)

Docker Compose Service Management.

```bash
# Up
sindri c up
sindri compose up

# Down
sindri c down
sindri compose down

# Restart
sindri c restart
sindri compose restart

# Build
sindri c build
sindri compose build

# Logs
sindri c logs
sindri compose logs

# Logs Tail
sindri c logs-tail
sindri compose logs-tail

# Status
sindri c ps
sindri compose ps

# Pull
sindri c pull
sindri compose pull
```

**Verfügbare Commands:**
- `compose-up` - Start Docker Compose services (detached mode)
- `compose-down` - Stop Docker Compose services
- `compose-restart` - Restart Docker Compose services
- `compose-build` - Build Docker Compose images
- `compose-logs` - Follow Docker Compose logs (Watch Mode)
- `compose-logs-tail` - Show last 100 lines of logs
- `compose-ps` - Show Docker Compose service status
- `compose-pull` - Pull Docker Compose images

### Git Commands (`g` / `git`)

Git Version Control Operations.

```bash
# Status
sindri g status
sindri git status

# Add All
sindri g add
sindri git add

# Commit
sindri g commit
sindri git commit

# Push
sindri g push
sindri git push

# Pull
sindri g pull
sindri git pull

# Log
sindri g log
sindri git log

# Monitor (kontinuierlich)
sindri g monitor
sindri git monitor

# Workflow (add, commit, push)
sindri g wf
sindri git wf

# Monitor GitHub Actions Run
sindri g wf --monitor
sindri git wf --monitor
```

**Verfügbare Commands:**
- `git-status` - Show working tree status
- `git-add` - Stage all changes
- `git-commit` - Stage and commit all changes
- `git-push` - Push commits to remote
- `git-pull` - Pull changes from remote
- `git-log` - Show recent commit history
- `git-monitor` - Continuously monitor Git status
- `git-wf` - Complete workflow (add, commit, push, optional monitor)

### Version Commands (`v` / `version`)

Version Management.

```bash
# Version anzeigen
sindri v show
sindri version show

# Version erhöhen
sindri v bump --patch
sindri version bump --patch
sindri version bump --minor
sindri version bump --major

# Git Tag erstellen
sindri v tag
sindri version tag
```

**Optionen:**
- `--patch` - Patch-Version erhöhen (0.1.4 → 0.1.5)
- `--minor` - Minor-Version erhöhen (0.1.4 → 0.2.0)
- `--major` - Major-Version erhöhen (0.1.4 → 1.0.0)

**Verfügbare Commands:**
- `version show` - Show current version from pyproject.toml
- `version bump` - Bump version number (updates pyproject.toml)
- `version tag` - Create git tag for current version

### Sindri Commands (`sindri`)

Sindri-spezifische Commands für Dokumentation.

```bash
# Docs Setup
sindri sindri docs-setup

# Docs Preview
sindri sindri docs-preview

# Docs Build
sindri sindri docs-build

# Docs Build (Strict)
sindri sindri docs-build-strict

# Docs Deploy
sindri sindri docs-deploy
```

**Verfügbare Commands:**
- `docs-setup` - Install documentation dependencies (MkDocs)
- `docs-preview` - Start local MkDocs server for preview (http://127.0.0.1:8000)
- `docs-build` - Build documentation site
- `docs-build-strict` - Build documentation site with strict mode
- `docs-deploy` - Deploy documentation to GitHub Pages

### Application Commands (`app` / `a` / `application`)

Application Lifecycle Management.

```bash
# Run application
sindri app run
sindri application run

# Run in development mode
sindri app dev
sindri application dev
```

**Verfügbare Commands:**
- `app-run` - Run the application
- `app-dev` - Run in development mode (with DEBUG=1)

### PyPI Commands (`p` / `pypi`)

PyPI Publishing Operations.

```bash
# Validate package
sindri p validate
sindri pypi validate

# Build and upload
sindri p push
sindri pypi push

# Upload to Test PyPI
sindri p push --test
sindri pypi push --test
```

**Verfügbare Commands:**
- `pypi-validate` - Validate package build and metadata
- `pypi-push` - Build and upload package to PyPI

**Optionen für `pypi-push`:**
- `--test` - Upload to Test PyPI instead of production
- `--repository <name>` - Use custom repository

## Verfügbare Namespaces

| Namespace | Alias | Beschreibung |
|-----------|-------|--------------|
| `quality` | `q` | Quality-Commands (lint, format, test) |
| `docker` | `d` | Docker-Commands |
| `compose` | `c`, `dc` | Docker Compose-Commands |
| `git` | `g` | Git-Commands |
| `version` | `v` | Version-Management |
| `sindri` | - | Sindri-spezifische Commands |
| `application` | `app`, `a` | Application-Commands |
| `pypi` | `p` | PyPI-Publishing |
| `general` | - | General setup commands |

## TUI Navigation

Die interaktive TUI bietet folgende Tastenkürzel:

- `Ctrl+F` oder `/`: Fokus auf Suchfeld
- `Enter`: Ausgewählten Command ausführen
- `↑/↓`: Durch Command-Liste navigieren
- `Tab`: Zwischen Panels wechseln
- `Ctrl+C` oder `Q`: Beenden
- `Esc`: Zurück zur Command-Liste

## Exit Codes

- `0`: Erfolgreich
- `1`: Fehler bei Command-Ausführung
- `2`: Command nicht gefunden
- `4`: Timeout
- `124`: Timeout (Unix)

## Beispiele

### Einfache Command-Ausführung

```bash
# Setup ausführen
sindri run setup

# Test mit Coverage
sindri q test-cov

# Docker Build
sindri d build
```

### Parallele Ausführung

```bash
# Mehrere Commands parallel
sindri run start web api --parallel

# Quality Checks parallel
sindri q lint format typecheck --parallel
```

### Git Workflow

```bash
# Kompletter Workflow: add, commit, push, monitor
sindri g wf --monitor
```

### Mit Timeout und Retries

```bash
# Test mit 60s Timeout und 2 Retries
sindri run test --timeout 60 --retries 2
```
