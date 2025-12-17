# Sindri Refactoring Plan

**Status:** Draft  
**Erstellt:** 2025-01-XX  
**Ziel:** Modernisierung der Architektur für Wartbarkeit, Erweiterbarkeit und Klarheit

---

## Executive Summary

Sindri ist ein solides Tool mit klarem Purpose, aber die aktuelle Architektur zeigt typische Wachstumsschmerzen:
- Zwei parallele Command-Systeme (Config vs. Implemented)
- Komplexe Loader-Logik mit zu vielen Verantwortlichkeiten
- Fehlende Plugin-Architektur für Erweiterungen
- CLI-Workarounds für dynamisches Command-Routing

Dieser Plan beschreibt einen inkrementellen Refactoring-Ansatz in 5 Phasen.

---

## Inhaltsverzeichnis

1. [Ist-Analyse](#1-ist-analyse)
2. [Ziel-Architektur](#2-ziel-architektur)
3. [Refactoring-Phasen](#3-refactoring-phasen)
4. [Migration Strategy](#4-migration-strategy)
5. [Testing Strategy](#5-testing-strategy)
6. [Risiken & Mitigationen](#6-risiken--mitigationen)

---

## 1. Ist-Analyse

### 1.1 Aktuelle Struktur

```
sindri/
├── cli/
│   ├── main.py           # Entry Point mit manuellem Arg-Parsing
│   ├── commands.py       # run(), list_commands(), init()
│   ├── parsing.py        # Command-Part-Parsing
│   └── ...
├── config/
│   ├── models.py         # Pydantic: Command, Group, SindriConfig
│   ├── loader.py         # Config Discovery + Loading + Group Expansion
│   └── implemented_commands.py  # Registry für Python-Commands
├── commands/
│   ├── command.py        # ABC Command (execute-basiert)
│   ├── shell_command.py  # ShellCommand Implementation
│   ├── group.py          # ABC CommandGroup
│   └── <group>/          # Docker, Git, Compose, etc.
├── runner/
│   ├── engine.py         # AsyncExecutionEngine
│   └── result.py         # CommandResult
└── utils/
```

### 1.2 Identifizierte Probleme

#### Problem 1: Duale Command-Repräsentation

| Aspekt | `config.models.Command` | `commands.command.Command` |
|--------|-------------------------|----------------------------|
| Typ | Pydantic Model | ABC |
| Quelle | TOML Config | Python Code |
| Ausführung | Via `shell` String | Via `execute()` Method |
| Verwendung | Runner | Custom Commands |

**Konsequenz:** `convert_to_config_command()` verliert Logik, `is_custom_command()` Check zur Runtime nötig.

#### Problem 2: Loader-Komplexität (250+ LOC)

`config/loader.py` macht zu viel:
- Config File Discovery (3 Strategien)
- TOML Parsing
- Group Reference Expansion
- Implemented Command Injection
- Environment Loading

#### Problem 3: Hardcoded Template Expansion

```python
# runner/engine.py
def _expand_templates(self, shell_cmd: str) -> str:
    shell_cmd = shell_cmd.replace("{registry}", registry)
    shell_cmd = shell_cmd.replace("${project_name}", project_name)
    return shell_cmd
```

Nicht erweiterbar, keine User-definierten Templates möglich.

#### Problem 4: CLI-Routing Workaround

`cli/main.py` parsed `sys.argv` manuell VOR Typer, um "unbekannte" Commands (wie `sindri docker build`) abzufangen. Das ist ein Workaround für fehlendes dynamisches CLI-Routing.

#### Problem 5: Keine Plugin-Architektur

Command Groups sind hardcoded:
```python
# commands/__init__.py
from sindri.commands.docker import DockerGroup
from sindri.commands.git import GitGroup
# ...
```

User können keine eigenen Groups registrieren.

---

## 2. Ziel-Architektur

### 2.1 Neue Struktur

```
sindri/
├── core/
│   ├── command.py          # Unified Command Protocol
│   ├── group.py            # CommandGroup (minimal)
│   ├── registry.py         # CommandRegistry (zentral)
│   ├── context.py          # ExecutionContext
│   ├── result.py           # CommandResult
│   └── templates.py        # Template Engine
├── config/
│   ├── schema.py           # Pydantic Models (nur Daten)
│   ├── discovery.py        # Config File Discovery
│   ├── loader.py           # TOML → Config (simplifiziert)
│   └── validator.py        # Config Validation
├── execution/
│   ├── engine.py           # Async Runner
│   ├── shell.py            # Shell Execution
│   └── pipeline.py         # Dependencies, Before/After
├── groups/                  # Built-in Command Groups
│   ├── __init__.py         # Auto-Discovery
│   ├── docker/
│   ├── git/
│   ├── compose/
│   ├── general/
│   ├── quality/
│   └── ...
├── cli/
│   ├── app.py              # Typer App
│   ├── router.py           # Dynamic Command Registration
│   └── display.py          # Output Formatting
├── plugins/                 # Plugin Entry Points
│   └── __init__.py         # Plugin Discovery
└── utils/
```

### 2.2 Kern-Design-Entscheidungen

#### 2.2.1 Unified Command Protocol

Ein Command-Interface für alle Quellen:

```python
# core/command.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class Command(Protocol):
    """Unified Command Protocol."""
    
    id: str
    title: str
    description: str | None
    group_id: str | None
    
    def get_shell(self, ctx: ExecutionContext) -> str | None:
        """Return shell command string, or None for custom execution."""
        ...
    
    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """Execute the command. Default impl runs get_shell()."""
        ...


@dataclass
class ShellCommand:
    """Default implementation for shell-based commands."""
    
    id: str
    shell: str
    title: str | None = None
    description: str | None = None
    group_id: str | None = None
    cwd: str | None = None
    env: dict[str, str] | None = None
    timeout: int | None = None
    
    def get_shell(self, ctx: ExecutionContext) -> str:
        return ctx.expand_templates(self.shell)
    
    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        shell = self.get_shell(ctx)
        return await ctx.engine.run_shell(shell, self.cwd, self.env)
```

#### 2.2.2 ExecutionContext

Alle Execution-Parameter gebündelt:

```python
# core/context.py
@dataclass
class ExecutionContext:
    """Execution context passed to all commands."""
    
    cwd: Path
    config: SindriConfig
    engine: ExecutionEngine
    env: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False
    verbose: bool = False
    
    def expand_templates(self, text: str) -> str:
        """Expand template variables in text."""
        return self.engine.template_engine.expand(text, self)
    
    def get_env(self, profile: str | None = None) -> dict[str, str]:
        """Get merged environment variables."""
        base = dict(os.environ)
        base.update(self.env)
        if profile:
            base.update(self.config.get_env_vars(profile))
        return base
```

#### 2.2.3 CommandRegistry

Zentrale Registry mit Plugin-Support:

```python
# core/registry.py
class CommandRegistry:
    """Central registry for all commands."""
    
    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._groups: dict[str, CommandGroup] = {}
        self._aliases: dict[str, str] = {}  # alias -> primary_id
    
    def register(self, command: Command) -> None:
        """Register a single command."""
        self._commands[command.id] = command
    
    def register_group(self, group: CommandGroup) -> None:
        """Register a command group with all its commands."""
        self._groups[group.id] = group
        for cmd in group.get_commands():
            cmd.group_id = group.id
            self.register(cmd)
    
    def load_from_config(self, config: SindriConfig) -> None:
        """Load commands from TOML config."""
        for cmd_data in config.commands:
            cmd = ShellCommand.from_config(cmd_data)
            self.register(cmd)
    
    def discover_plugins(self) -> None:
        """Discover and load plugin command groups."""
        for entry_point in importlib.metadata.entry_points(group='sindri.groups'):
            group_class = entry_point.load()
            self.register_group(group_class())
    
    def get(self, id_or_alias: str) -> Command | None:
        """Get command by ID or alias."""
        if id_or_alias in self._aliases:
            id_or_alias = self._aliases[id_or_alias]
        return self._commands.get(id_or_alias)
    
    def resolve_parts(self, parts: list[str]) -> Command | None:
        """Resolve command from CLI parts (e.g., ['docker', 'build'])."""
        # Try full ID first: "docker-build"
        full_id = "-".join(parts)
        if cmd := self.get(full_id):
            return cmd
        # Try namespace lookup
        if len(parts) == 2:
            namespace, action = parts
            return self.get(f"{namespace}-{action}")
        return None
```

#### 2.2.4 Template Engine

Erweiterbare Template-Expansion:

```python
# core/templates.py
class TemplateEngine:
    """Extensible template expansion."""
    
    def __init__(self):
        self._resolvers: dict[str, Callable[[ExecutionContext], str]] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        self.register("project_name", lambda ctx: ctx.config.project_name or ctx.cwd.name)
        self.register("registry", lambda ctx: ctx.config.defaults.docker_registry)
        self.register("version", lambda ctx: get_project_version(ctx.cwd))
    
    def register(self, name: str, resolver: Callable[[ExecutionContext], str]):
        """Register a template variable resolver."""
        self._resolvers[name] = resolver
    
    def expand(self, text: str, ctx: ExecutionContext) -> str:
        """Expand all template variables in text."""
        result = text
        for name, resolver in self._resolvers.items():
            patterns = [f"{{{name}}}", f"${{{name}}}"]
            for pattern in patterns:
                if pattern in result:
                    result = result.replace(pattern, resolver(ctx))
        return result
```

---

## 3. Refactoring-Phasen

### Phase 1: Core Foundation (Week 1-2)

**Ziel:** Neue Core-Module ohne Breaking Changes einführen.

#### Tasks

1. **Create `core/` module**
   - [ ] `core/__init__.py`
   - [ ] `core/result.py` (move from `runner/result.py`)
   - [ ] `core/context.py` (new)
   - [ ] `core/templates.py` (new)

2. **Implement ExecutionContext**
   ```python
   # Kann parallel zu bestehendem Code existieren
   @dataclass
   class ExecutionContext:
       cwd: Path
       config: SindriConfig
       env: dict[str, str] = field(default_factory=dict)
       dry_run: bool = False
   ```

3. **Implement TemplateEngine**
   - Extrahiere Logic aus `engine._expand_templates()`
   - Mache erweiterbar via `register()`

4. **Tests**
   - [ ] `tests/test_context.py`
   - [ ] `tests/test_templates.py`

#### Acceptance Criteria
- Alle bestehenden Tests grün
- Neue Module importierbar
- Template-Expansion via Engine funktioniert

---

### Phase 2: Command Unification (Week 3-4)

**Ziel:** Unified Command Protocol einführen, Dual-System eliminieren.

#### Tasks

1. **Create Command Protocol**
   ```python
   # core/command.py
   @runtime_checkable
   class Command(Protocol):
       id: str
       title: str
       description: str | None
       
       def get_shell(self, ctx: ExecutionContext) -> str | None: ...
       async def execute(self, ctx: ExecutionContext) -> CommandResult: ...
   ```

2. **Adapt ShellCommand**
   - Implementiere Protocol
   - Add `from_config()` class method
   - Deprecate old `config.models.Command` usage

3. **Migrate Custom Commands**
   - `DockerBuildCommand` → implements Protocol
   - `DockerPushCommand` → implements Protocol
   - etc.

4. **Update Engine**
   - `run_command(cmd: Command, ctx: ExecutionContext)`
   - Remove `is_custom_command()` check

5. **Deprecate old classes**
   - Add `@deprecated` decorator to old Command ABC
   - Add migration warnings

#### Acceptance Criteria
- Alle Commands implementieren Protocol
- `is_custom_command()` entfernt
- `convert_to_config_command()` entfernt

---

### Phase 3: Registry & Plugin System (Week 5-6)

**Ziel:** Zentrale Registry mit Plugin-Support.

#### Tasks

1. **Implement CommandRegistry**
   ```python
   registry = CommandRegistry()
   registry.register_group(DockerGroup())
   registry.load_from_config(config)
   registry.discover_plugins()
   ```

2. **Refactor Loader**
   - Split `loader.py`:
     - `discovery.py` - Config file discovery
     - `loader.py` - TOML parsing only
     - `validator.py` - Validation logic
   - Remove group expansion from loader (Registry's job)

3. **Plugin Entry Points**
   ```toml
   # pyproject.toml
   [project.entry-points."sindri.groups"]
   my-group = "my_package:MyGroup"
   ```

4. **Auto-Discovery for Built-in Groups**
   ```python
   # groups/__init__.py
   def discover_builtin_groups() -> list[CommandGroup]:
       """Auto-discover all built-in groups."""
       groups = []
       for module in pkgutil.iter_modules(__path__):
           # ... load group class
       return groups
   ```

5. **Update CLI to use Registry**

#### Acceptance Criteria
- Loader unter 100 LOC
- Plugin Groups registrierbar
- Built-in Groups auto-discovered

---

### Phase 4: CLI Modernization (Week 7-8)

**Ziel:** Sauberes CLI-Routing ohne Workarounds.

#### Tasks

1. **Dynamic Command Registration**
   ```python
   # cli/router.py
   def register_commands(app: typer.Typer, registry: CommandRegistry):
       """Dynamically register commands from registry."""
       for group in registry.groups.values():
           group_app = typer.Typer(name=group.id, help=group.description)
           for cmd in group.get_commands():
               @group_app.command(name=cmd.id.split("-")[-1])
               def run_cmd(cmd=cmd):
                   # ... execute
           app.add_typer(group_app)
   ```

2. **Remove Manual Arg Parsing**
   - Delete `_parse_args()` in `main.py`
   - Let Typer handle everything

3. **Improve Help Output**
   - Group commands by category
   - Show aliases

4. **Add Completion Support**
   ```python
   app.add_completion()
   ```

#### Acceptance Criteria
- `cli/main.py` unter 50 LOC
- Keine manuelle `sys.argv` Manipulation
- Shell Completion funktioniert

---

### Phase 5: Cleanup & Documentation (Week 9-10)

**Ziel:** Alte Codepfade entfernen, Docs aktualisieren.

#### Tasks

1. **Remove Deprecated Code**
   - [ ] Old `commands/command.py` ABC
   - [ ] `config/implemented_commands.py`
   - [ ] `convert_to_config_command()`
   - [ ] `is_custom_command()`

2. **Update Documentation**
   - [ ] README.md - Architecture section
   - [ ] CONTRIBUTING.md - How to add commands
   - [ ] Plugin documentation

3. **Migration Guide**
   - [ ] `MIGRATION.md` für Plugin-Autoren

4. **Performance Audit**
   - Startup time measurement
   - Registry lookup benchmarks

5. **Final Test Suite Review**
   - Coverage target: 90%
   - Integration tests for all groups

#### Acceptance Criteria
- Keine deprecated code paths
- Docs aktuell
- Test coverage ≥ 90%

---

## 4. Migration Strategy

### 4.1 Backward Compatibility

| Version | Breaking Changes | Support |
|---------|------------------|---------|
| 0.2.x | None | Full backward compat |
| 0.3.x | Deprecation warnings | Old API still works |
| 0.4.x | Old API removed | Migration required |

### 4.2 Config File Compatibility

Bestehende `sindri.toml` Files bleiben kompatibel. Neue Features opt-in:

```toml
# Old format still works
[[commands]]
id = "build"
shell = "make build"

# New format (optional)
[sindri]
version = "2.0"  # Opt-in to new features

[sindri.templates]
custom_var = "value"
```

### 4.3 API Versioning

```python
# sindri/__init__.py
__version__ = "0.2.0"
__api_version__ = "1"  # Increment on breaking changes
```

---

## 5. Testing Strategy

### 5.1 Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| Unit | `tests/unit/` | Isolated component tests |
| Integration | `tests/integration/` | Cross-component tests |
| E2E | `tests/e2e/` | Full CLI tests |
| Regression | `tests/regression/` | Bug reproduction |

### 5.2 Test Fixtures

```python
# tests/conftest.py
@pytest.fixture
def registry():
    """Pre-populated command registry."""
    reg = CommandRegistry()
    reg.register_group(DockerGroup())
    return reg

@pytest.fixture
def context(tmp_path):
    """Execution context with temp directory."""
    return ExecutionContext(
        cwd=tmp_path,
        config=SindriConfig(commands=[]),
    )
```

### 5.3 Coverage Requirements

- Core modules: ≥ 95%
- CLI modules: ≥ 80%
- Groups: ≥ 85%
- Overall: ≥ 90%

---

## 6. Risiken & Mitigationen

### Risk 1: Breaking User Configs

**Wahrscheinlichkeit:** Mittel  
**Impact:** Hoch  
**Mitigation:**
- Config schema versioning
- Validator mit hilfreichen Migration-Hints
- `sindri config migrate` Command

### Risk 2: Plugin API Instabilität

**Wahrscheinlichkeit:** Mittel  
**Impact:** Mittel  
**Mitigation:**
- Protocol-based API (duck typing)
- Semantic versioning für API
- Deprecation warnings vor Breaking Changes

### Risk 3: Performance Regression

**Wahrscheinlichkeit:** Niedrig  
**Impact:** Mittel  
**Mitigation:**
- Startup time benchmarks in CI
- Lazy loading für Groups
- Registry caching

### Risk 4: Scope Creep

**Wahrscheinlichkeit:** Hoch  
**Impact:** Mittel  
**Mitigation:**
- Strikt phasenbasiertes Vorgehen
- Feature freeze während Refactoring
- Klare Acceptance Criteria pro Phase

---

## Appendix A: File Changes Summary

### New Files

```
sindri/core/__init__.py
sindri/core/command.py
sindri/core/context.py
sindri/core/registry.py
sindri/core/templates.py
sindri/config/discovery.py
sindri/config/validator.py
sindri/cli/router.py
sindri/plugins/__init__.py
```

### Modified Files

```
sindri/config/loader.py      # Simplified
sindri/config/models.py      # Renamed to schema.py
sindri/runner/engine.py      # Use ExecutionContext
sindri/cli/main.py           # Use Router
sindri/cli/commands.py       # Use Registry
sindri/commands/*            # Implement Protocol
```

### Deleted Files (Phase 5)

```
sindri/config/implemented_commands.py
sindri/commands/command.py   # Old ABC (replaced by core/command.py)
```

---

## Appendix B: Command Protocol Reference

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@runtime_checkable
class Command(Protocol):
    """
    Unified Command Protocol.
    
    All commands (shell-based, custom, plugin) implement this protocol.
    """
    
    @property
    def id(self) -> str:
        """Unique command identifier (e.g., 'docker-build')."""
        ...
    
    @property
    def title(self) -> str:
        """Human-readable title."""
        ...
    
    @property
    def description(self) -> str | None:
        """Optional description."""
        ...
    
    @property
    def group_id(self) -> str | None:
        """Optional group membership."""
        ...
    
    def get_shell(self, ctx: ExecutionContext) -> str | None:
        """
        Return shell command string.
        
        Returns None if command requires custom execution logic.
        Template variables are expanded by the caller.
        """
        ...
    
    async def execute(self, ctx: ExecutionContext) -> CommandResult:
        """
        Execute the command.
        
        Default implementation runs get_shell() via the engine.
        Override for custom execution logic.
        """
        ...
    
    def validate(self, ctx: ExecutionContext) -> str | None:
        """
        Validate command can run in given context.
        
        Returns error message if invalid, None if valid.
        """
        ...
```

---

## Appendix C: Entscheidungslog

| Datum | Entscheidung | Begründung |
|-------|--------------|------------|
| TBD | Protocol statt ABC | Flexibler, ermöglicht dataclasses |
| TBD | Entry Points für Plugins | Standard Python Mechanismus |
| TBD | Phasen-basiertes Refactoring | Risiko-Minimierung |

---

## Next Steps

1. [ ] Review dieses Plans im Team
2. [ ] Priorisierung der Phasen bestätigen
3. [ ] Phase 1 Branch erstellen
4. [ ] Erste PRs für Core-Module
