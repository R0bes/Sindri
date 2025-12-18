# CLI Referenz

Vollständige Referenz aller CLI-Befehle und Optionen.

## `sindri init`

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

## `sindri run <command-id>`

Führt einen oder mehrere Commands nicht-interaktiv aus.

```bash
sindri run setup
sindri run start web api --parallel
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

## `sindri list`

Listet alle verfügbaren Commands auf.

```bash
sindri list
sindri list --config custom.toml
```

**Optionen:**
- `--config, -c`: Pfad zur Config-Datei

## `sindri` (Standard)

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

Sindri unterstützt Namespace-Commands für Built-in-Gruppen:

```bash
# Quality Commands
sindri q test
sindri q test-cov
sindri quality test

# Docker Commands
sindri d build
sindri docker build

# Git Commands
sindri g commit
sindri git commit

# Version Commands
sindri version bump --patch
sindri version show
```

### Verfügbare Namespaces

- `q` / `quality`: Quality-Commands
- `d` / `docker`: Docker-Commands
- `c` / `compose`: Docker Compose-Commands
- `g` / `git`: Git-Commands
- `version`: Version-Management

## TUI Navigation

Die interaktive TUI bietet folgende Tastenkürzel:

- `Ctrl+F` oder `/`: Fokus auf Suchfeld
- `Enter`: Ausgewählten Command ausführen
- `↑/↓`: Durch Command-Liste navigieren
- `Tab`: Zwischen Panels wechseln
- `Ctrl+C` oder `Q`: Beenden

## Exit Codes

- `0`: Erfolgreich
- `1`: Fehler bei Command-Ausführung
- `2`: Command nicht gefunden
- `4`: Timeout

