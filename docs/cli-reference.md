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

# Run
sindri d run
sindri docker run

# Push
sindri d push
sindri docker push
```

### Docker Compose Commands (`c` / `compose`)

Docker Compose Service Management.

```bash
# Up
sindri c up
sindri compose up

# Down
sindri c down
sindri compose down

# Logs
sindri c logs
sindri compose logs
```

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

### Version Commands (`version`)

Version Management.

```bash
# Version anzeigen
sindri version show

# Version erhöhen
sindri version bump --patch
sindri version bump --minor
sindri version bump --major
```

**Optionen:**
- `--patch` - Patch-Version erhöhen (0.1.4 → 0.1.5)
- `--minor` - Minor-Version erhöhen (0.1.4 → 0.2.0)
- `--major` - Major-Version erhöhen (0.1.4 → 1.0.0)

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

### Application Commands (`app` / `application`)

Application Lifecycle Management.

```bash
sindri app start
sindri application start

sindri app stop
sindri application stop

sindri app restart
sindri application restart
```

### PyPI Commands (`p` / `pypi`)

PyPI Publishing Operations.

```bash
sindri p build
sindri pypi build

sindri p upload
sindri pypi upload
```

## Verfügbare Namespaces

| Namespace | Alias | Beschreibung |
|-----------|-------|--------------|
| `quality` | `q` | Quality-Commands (lint, format, test) |
| `docker` | `d` | Docker-Commands |
| `compose` | `c` | Docker Compose-Commands |
| `git` | `g` | Git-Commands |
| `version` | - | Version-Management |
| `sindri` | - | Sindri-spezifische Commands |
| `application` | `app`, `a` | Application-Commands |
| `pypi` | `p` | PyPI-Publishing |

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
