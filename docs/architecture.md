# Architektur

Überblick über die Systemarchitektur und Design-Entscheidungen von Sindri.

## Architektur-Übersicht

Sindri folgt einer **klaren Schichtenarchitektur**:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Layer (Typer)                        │
│  - main.py, commands.py, parsing.py, display.py             │
│  - subcommands.py, interactive_init.py                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Layer                               │
│  - Registry (Command-Verwaltung)                           │
│  - ExecutionContext (Template-Integration)                │
│  - Command Protocol (ShellCommand, CustomCommand)           │
│  - ShellRunner (Async Execution)                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Groups Layer                              │
│  - 9 Built-in Command Groups                                │
│  - Plugin-Support via Entry Points                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Config Layer                              │
│  - TOML Loader (Pydantic Models)                            │
│  - Config Discovery                                          │
└─────────────────────────────────────────────────────────────┘
```

## Komponenten

### CLI Layer

**Verantwortlichkeiten:**
- Argument-Parsing und Validierung
- Command-Discovery und -Routing
- User-Interface (CLI und TUI)
- Interaktive Initialisierung

**Hauptmodule:**
- `main.py`: Entry Point und Command-Routing
- `commands.py`: Haupt-Commands (init, run, list)
- `parsing.py`: Command-Parsing und -Auflösung
- `display.py`: Formatierung und Ausgabe
- `subcommands.py`: Namespace-Subcommands
- `interactive_init.py`: Interaktive Config-Erstellung

### Core Layer

**Verantwortlichkeiten:**
- Command-Registry und -Verwaltung
- Command-Execution (async)
- Template-Expansion
- Result-Handling

**Hauptmodule:**
- `registry.py`: Zentrale Command-Registry
- `command.py`: Command-Protocol und Implementierungen
- `shell_runner.py`: Async Command-Execution
- `context.py`: Execution-Context mit Templates
- `result.py`: Command-Result-Modelle
- `templates.py`: Template-Engine

### Groups Layer

**Verantwortlichkeiten:**
- Built-in Command-Gruppen
- Plugin-System
- Group-Discovery

**Verfügbare Groups:**
- `quality`: Test- und Quality-Commands
- `docker`: Docker-Commands
- `compose`: Docker Compose-Commands
- `git`: Git-Commands
- `version`: Version-Management
- `pypi`: PyPI-Publishing
- `application`: Application-Commands
- `general`: Allgemeine Commands
- `sindri`: Sindri-spezifische Commands

### Config Layer

**Verantwortlichkeiten:**
- Config-Discovery (TOML-Dateien)
- Config-Validierung (Pydantic)
- Config-Loading

**Hauptmodule:**
- `loader.py`: Config-Discovery und -Loading
- `models.py`: Pydantic-Modelle für Config

## Design-Prinzipien

### 1. Separation of Concerns

Jede Schicht hat klare Verantwortlichkeiten und ist unabhängig testbar.

### 2. Protocol-Based Design

Commands implementieren ein Protocol, nicht eine Basisklasse. Dies ermöglicht Flexibilität und einfache Erweiterung.

### 3. Registry Pattern

Zentrale Registry für alle Commands ermöglicht einfache Discovery und Verwaltung.

### 4. Async-First

Command-Execution ist von Grund auf async, ermöglicht parallele Ausführung und Streaming.

### 5. Template-Engine

Variablen-Expansion in Commands ermöglicht dynamische Command-Generierung.

## Erweiterbarkeit

### Custom Commands

Commands können über die Config definiert werden:

```toml
[[commands]]
id = "custom"
shell = "echo $VAR"
env = { VAR = "value" }
```

### Custom Groups

Groups können über Entry Points registriert werden:

```python
# setup.py oder pyproject.toml
[project.entry-points."sindri.groups"]
mygroup = "mypackage.groups:MyGroup"
```

### Plugin-System

Plugins können neue Command-Typen, Groups oder Features hinzufügen.

## Datenfluss

1. **Config Loading**: Config wird geladen und validiert
2. **Registry Initialization**: Commands werden in Registry registriert
3. **Command Discovery**: User-Command wird aufgelöst
4. **Execution**: Command wird asynchron ausgeführt
5. **Result Handling**: Result wird verarbeitet und angezeigt

## Performance

- **Lazy Loading**: Commands werden nur bei Bedarf geladen
- **Async Execution**: Parallele Ausführung mehrerer Commands
- **Streaming**: Live-Output während der Ausführung
- **Caching**: Config wird gecacht, um wiederholte Disk-IO zu vermeiden

## Sicherheit

- **Shell-Escaping**: User-Input wird escaped
- **Config-Validation**: Pydantic validiert alle Config-Werte
- **Sandboxing**: Commands laufen im aktuellen Prozess-Kontext

