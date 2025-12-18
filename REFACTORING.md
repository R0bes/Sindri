# Sindri Refactoring Plan

**Status:** In Progress  
**Erstellt:** 2025-01  
**Letzte Aktualisierung:** 2025-01  
**Ziel:** Modernisierung der Architektur für Wartbarkeit, Erweiterbarkeit und Klarheit

---

## Executive Summary

Sindri ist ein solides Tool mit klarem Purpose. Der Großteil des Refactorings ist abgeschlossen. Dieser Plan dokumentiert den aktuellen Stand und die verbleibenden Aufgaben.

---

## Fortschritts-Übersicht

| Phase | Status | Beschreibung |
|-------|--------|--------------|
| Phase 1: Core Foundation | ✅ **Abgeschlossen** | `core/` Module implementiert |
| Phase 2: Command Unification | ✅ **Abgeschlossen** | Alle Groups migriert nach `groups/` |
| Phase 3: Registry & Loader | ✅ **Abgeschlossen** | Loader vereinfacht, CLI nutzt Registry |
| Phase 4: CLI Modernization | ✅ **Abgeschlossen** | Registry integriert, CLI nutzt Typer App direkt |
| Phase 5: Cleanup & Documentation | ✅ **Abgeschlossen** | `runner/` gelöscht, Tests aktualisiert |

---

## Aktueller Stand der Implementierung

### ✅ Phase 1-3: Vollständig abgeschlossen

#### Core Module (`sindri/core/`)

```
sindri/core/
├── __init__.py      ✅ Sauber exportiert
├── command.py       ✅ Command Protocol + ShellCommand + CustomCommand
├── context.py       ✅ ExecutionContext mit Template-Integration
├── group.py         ✅ CommandGroup ABC
├── registry.py      ✅ CommandRegistry mit Plugin-Support
├── result.py        ✅ CommandResult
├── shell.py         ✅ Shell utilities
├── shell_runner.py  ✅ Async shell execution
└── templates.py     ✅ Erweiterbare TemplateEngine
```

#### Groups (`sindri/groups/`) - **VOLLSTÄNDIG**

```
sindri/groups/
├── __init__.py        ✅ get_all_builtin_groups()
├── general.py         ✅ ShellCommands
├── quality.py         ✅ ShellCommands
├── application.py     ✅ ShellCommands
├── docker.py          ✅ CustomCommands (Build, Push, BuildAndPush)
├── compose.py         ✅ ShellCommands
├── git.py             ✅ ShellCommands
├── version.py         ✅ CustomCommands (Show, Bump, Tag)
├── pypi.py            ✅ CustomCommands (Validate, Push)
└── sindri_group.py    ✅ Leere Group
```

#### Config (`sindri/config/`) - **VEREINFACHT**

```
sindri/config/
├── __init__.py               ✅ Saubere Exports
├── loader.py                 ✅ Vereinfacht (~100 LOC)
├── models.py                 ✅ Pydantic Models
└── implemented_commands.py   ✅ GELÖSCHT
```

**Änderungen am Loader:**
- Entfernt: `get_implemented_commands()` Import
- Entfernt: `convert_to_config_command()` Import
- Entfernt: Komplexe Group-Expansion-Logic
- Loader lädt jetzt NUR TOML, keine Command-Injection mehr
- Registry ist verantwortlich für Command-Loading

#### CLI (`sindri/cli/commands.py`) - **AKTUALISIERT**

**Neue Funktionen:**
- `_init_registry()` - Initialisiert Registry mit builtin Groups + Config
- `run()` - Nutzt Registry zum Auflösen von Commands
- `_print_registry_commands()` - Zeigt Commands aus Registry an
- Commands werden direkt via `cmd.execute(ctx)` ausgeführt

**Entfernt:**
- Import von `implemented_commands`
- `is_custom_command()` Check
- Alte `AsyncExecutionEngine` Nutzung für Custom Commands

---

### 🟡 Phase 4: CLI Modernization (Teilweise)

#### Was fertig ist:
- ✅ `cli/commands.py` nutzt Registry
- ✅ Commands werden via `ExecutionContext` ausgeführt
- ✅ Custom Commands werden erkannt via `isinstance(cmd, CustomCommand)`

#### Status:
- ✅ `cli/commands.py` nutzt Registry
- ✅ `cli/__init__.py` nutzt Typer App direkt
- ⚠️ `cli/main.py` - Wird noch in pyproject.toml referenziert, aber Logik ist in `__init__.py`
- ⚠️ `cli/parsing.py` - Wird noch verwendet, aber könnte vereinfacht werden
- ❌ Dynamic Command Registration für Typer (optional, low priority)

---

### ✅ Phase 5: Cleanup (Abgeschlossen)

#### Gelöschte Dateien:

```bash
# Legacy commands/ Ordner (komplett) - ✅ GELÖSCHT
# sindri/commands/ - wurde bereits gelöscht

# Deprecated config file - ✅ GELÖSCHT
# sindri/config/implemented_commands.py - wurde bereits gelöscht

# Legacy runner/ Ordner - ✅ GELÖSCHT
sindri/runner/engine.py
sindri/runner/result.py
sindri/runner/__init__.py
```

#### Aktualisierte Tests:
- ✅ `tests/test_runner.py` - Umgestellt auf `run_shell_command` aus `core/shell_runner`
- ✅ `tests/test_integration.py` - Umgestellt auf neue Architektur mit Registry und ExecutionContext
- ✅ `tests/unit/test_result.py` - Backward-Compatibility-Tests entfernt

#### Zu aktualisierende Imports:

Suche nach:
```python
from sindri.commands import ...
from sindri.commands.command import ...
from sindri.commands.group import ...
```

Ersetze durch:
```python
from sindri.core import ...
from sindri.groups import ...
```

---

## Architektur-Diagramm (Aktuell)

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  main   │  │commands │  │ parsing │  │ display │        │
│  └────┬────┘  └────┬────┘  └─────────┘  └─────────┘        │
│       │            │                                        │
│       │     ┌──────┴──────┐                                 │
│       │     │  Registry   │ ◄── Zentrale Command-Verwaltung │
│       │     └──────┬──────┘                                 │
└───────┼────────────┼────────────────────────────────────────┘
        │            │
        ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                       Core Layer ✅                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Registry   │  │   Context    │  │  Templates   │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Command    │  │ ShellRunner  │                        │
│  │  (protocol)  │  │   (async)    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Groups Layer ✅                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │ docker │ │  git   │ │compose │ │version │ │  pypi  │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐              │
│  │general │ │quality │ │  app   │ │ sindri │              │
│  └────────┘ └────────┘ └────────┘ └────────┘              │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Config Layer ✅                           │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Loader     │  │   Models     │                        │
│  │ (nur TOML)   │  │  (Pydantic)  │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Checkliste für Vollständige Migration

```
Core Foundation
  ✅ core/command.py     - Command Protocol
  ✅ core/context.py     - ExecutionContext
  ✅ core/registry.py    - CommandRegistry
  ✅ core/templates.py   - TemplateEngine
  ✅ core/result.py      - CommandResult
  ✅ core/shell_runner.py - Async Shell Execution
  ✅ core/group.py       - CommandGroup ABC

Groups Migration
  ✅ groups/general.py
  ✅ groups/quality.py
  ✅ groups/application.py
  ✅ groups/docker.py
  ✅ groups/compose.py
  ✅ groups/git.py
  ✅ groups/version.py
  ✅ groups/pypi.py
  ✅ groups/sindri_group.py

Config Simplification
  ✅ Loader vereinfacht (nur TOML laden)
  ✅ CLI nutzt Registry für Commands
  ✅ implemented_commands.py gelöscht
  ✅ Alle deprecated Code entfernt

CLI Modernization
  ✅ commands.py nutzt Registry
  ✅ ExecutionContext für Command-Ausführung
  ❌ main.py noch mit manuellem Arg-Parsing
  ❌ Typer Dynamic Commands

Cleanup
  ✅ Lösche alte commands/ (bereits gelöscht)
  ✅ Lösche runner/ (bereits gelöscht)
  ✅ Update Tests (bereits aktualisiert)
  ✅ Entferne deprecated Code und Backwards-Compatibility
  ✅ Entferne get_default_engine Alias
  ✅ Entferne Backward-Compatibility-Tests
  ❌ Update Dokumentation
```

---

## Nächste Schritte

### Sofort (High Priority)

1. **Testen:** `sindri` CLI testen, ob alles funktioniert
2. **Cleanup:** `sindri/commands/` Ordner löschen (nach Test)
3. **Cleanup:** `sindri/config/implemented_commands.py` löschen

### Mittelfristig (Medium Priority)

4. **CLI main.py:** Manuelles Arg-Parsing entfernen
5. **Tests:** Auf neue Imports umstellen

### Optional (Low Priority)

6. **Typer Dynamic Commands:** Für bessere CLI-Struktur
7. **Plugin Entry Points:** Dokumentieren und testen

---

## Appendix: Import-Pfad-Referenz

### Neue (korrekte) Imports

```python
# Commands & Execution
from sindri.core import (
    Command, 
    ShellCommand, 
    CustomCommand,
    CommandGroup,
    CommandRegistry, 
    get_registry,
    ExecutionContext,
    CommandResult,
    run_shell_command,
    TemplateEngine, 
    get_template_engine,
)

# Built-in Groups
from sindri.groups import (
    DockerGroup, 
    ComposeGroup,
    GitGroup, 
    VersionGroup,
    PyPIGroup,
    GeneralGroup,
    QualityGroup,
    ApplicationGroup,
    SindriGroup,
)

# Config (nur für TOML-Loading)
from sindri.config import (
    load_config,
    get_config_dir,
    SindriConfig,
)
```

### Alte (NICHT MEHR VERWENDEN - ALLE ENTFERNT)

```python
# ENTFERNT - Keine deprecated Imports mehr vorhanden:
# from sindri.commands import Command, ShellCommand
# from sindri.commands.command import Command
# from sindri.commands.group import CommandGroup
# from sindri.config.implemented_commands import get_implemented_commands
# from sindri.runner import CommandResult
# from sindri.runner.result import CommandResult
```

---

## Änderungshistorie

| Datum | Änderung |
|-------|----------|
| 2025-01 | Phase 1: Core Foundation abgeschlossen |
| 2025-01 | Phase 2: Alle Groups nach `groups/` migriert |
| 2025-01 | Phase 3: Loader vereinfacht, CLI auf Registry umgestellt |
