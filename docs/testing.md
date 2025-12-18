# Testing

Test-Strategie und Coverage-Informationen für Sindri.

## Test-Übersicht

**Gesamt:** 195+ Tests über 10+ Test-Dateien

| Modul | Tests | Coverage | Status |
|-------|-------|----------|--------|
| CLI | 50+ | 83.35% | ⚠️ |
| Config | 30+ | ~95% | ✅ |
| Core | 20+ | ~90% | ✅ |
| Utils | 15+ | ~95% | ✅ |
| Groups | 10+ | ~95% | ✅ |
| Integration | 5+ | ~85% | ✅ |

## Test-Struktur

```
tests/
├── conftest.py              # Zentrale Fixtures
├── test_cli.py              # CLI-Tests
├── test_cli_additional.py   # Erweiterte CLI-Tests
├── test_cli_95_coverage.py  # Coverage-Tests
├── test_cli_direct_callbacks.py  # Callback-Tests
├── test_config.py           # Config-Tests
├── test_runner.py           # Runner-Tests
├── test_utils.py            # Utils-Tests
├── test_logging.py          # Logging-Tests
├── test_integration.py      # Integration-Tests
└── unit/                    # Unit-Tests
```

## Fixtures

Zentrale Fixtures in `tests/conftest.py`:

- `temp_dir`: Temporäres Verzeichnis für Tests
- `sample_config`: Beispiel-Konfiguration
- `sample_command`: Beispiel-Command
- `cli_runner`: Typer CLI Runner

## Tests ausführen

### Alle Tests

```bash
pytest
```

### Mit Coverage

```bash
pytest --cov=sindri --cov-report=html
```

### Spezifische Module

```bash
pytest tests/test_cli.py
pytest tests/test_config.py
```

### Mit Verbose Output

```bash
pytest -v
```

### Nur schnelle Tests

```bash
pytest -m "not integration"
```

## Coverage-Ziel

- **Ziel**: 90%+ Code Coverage
- **Aktuell**: 
  - CLI-Modul: 83.35%
  - Gesamt: ~85%

### Coverage-Berichte

```bash
# Terminal-Bericht
pytest --cov=sindri --cov-report=term-missing

# HTML-Bericht
pytest --cov=sindri --cov-report=html
# Öffnet htmlcov/index.html
```

## Test-Typen

### Unit Tests

Isolierte Komponenten-Tests ohne externe Abhängigkeiten.

**Beispiel:**
```python
def test_command_creation():
    cmd = Command(id="test", shell="echo test")
    assert cmd.id == "test"
```

### Integration Tests

Tests für das Zusammenspiel mehrerer Module.

**Beispiel:**
```python
def test_config_loading_and_execution(temp_dir):
    config = load_config(temp_dir / "sindri.toml")
    result = run_command(config, "test")
    assert result.success
```

### CLI Tests

End-to-End Tests für CLI-Befehle.

**Beispiel:**
```python
def test_init_command(cli_runner, temp_dir):
    result = cli_runner.invoke(app, ["init"])
    assert result.exit_code == 0
```

## Best Practices

1. **Fixtures verwenden**: Zentrale Fixtures für Wiederverwendbarkeit
2. **Isolation**: Tests sollten unabhängig voneinander sein
3. **Edge Cases**: Auch ungewöhnliche Szenarien testen
4. **Mocking**: Wo nötig (z.B. File-System, Shell-Commands)
5. **Platform-spezifisch**: Windows/Unix-Unterschiede berücksichtigen

## Coverage-Verbesserungen

### Aktuelle Lücken

- `subcommands.py`: 65% (Zeilen 69-116, 196-199)
- `main.py`: 82% (Zeilen 154-178, 186-190, 240)
- `__init__.py`: 81% (Zeilen 141, 149-150, 153-154, 157-158, 177-181)

### Geplante Verbesserungen

1. Tests für Callback-Funktionen in `subcommands.py`
2. Tests für Namespace-Hilfe in `main.py`
3. Tests für Argument-Filterung in `__init__.py`

## CI/CD Integration

Tests werden automatisch in GitHub Actions ausgeführt:

- Multi-OS: Ubuntu, Windows, macOS
- Multi-Python: 3.11, 3.12, 3.13
- Coverage-Upload zu Codecov

Siehe [.github/workflows/ci.yml](https://github.com/yourusername/sindri/blob/main/.github/workflows/ci.yml) für Details.

