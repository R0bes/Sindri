# Development Guide

Guide für Entwickler, die zu Sindri beitragen möchten.

## Setup

### Repository klonen

```bash
git clone https://github.com/yourusername/sindri.git
cd sindri
```

### Virtual Environment erstellen

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Dependencies installieren

```bash
pip install -e ".[dev]"
```

## Projektstruktur

```
sindri/
├── sindri/                    # Hauptpaket
│   ├── cli/                   # CLI-Interface
│   ├── config/                # Konfiguration
│   ├── core/                  # Kern-Funktionalität
│   ├── groups/                # Command Groups
│   └── utils/                 # Utilities
├── tests/                     # Test-Suite
│   ├── unit/                  # Unit-Tests
│   └── conftest.py            # Zentrale Fixtures
├── examples/                  # Beispiel-Konfigurationen
├── docs/                      # Dokumentation
└── pyproject.toml             # Projekt-Konfiguration
```

## Entwicklung

### Code-Stil

- **Linting**: Ruff
- **Formatting**: Ruff (Black-kompatibel)
- **Type Hints**: Umfassend verwendet
- **Docstrings**: Google-Style

### Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=sindri --cov-report=html

# Spezifische Test-Datei
pytest tests/test_config.py

# Mit Verbose Output
pytest -v
```

### Linting

```bash
# Ruff check
ruff check sindri/ tests/

# Ruff format
ruff format sindri/ tests/
```

### Type Checking

```bash
mypy sindri/
```

## Test-Strategie

### Coverage-Ziel

- **Ziel**: 90%+ Code Coverage
- **Aktuell**: ~83% (CLI-Modul)

### Test-Typen

1. **Unit Tests**: Isolierte Komponenten-Tests
2. **Integration Tests**: Zusammenspiel mehrerer Module
3. **CLI Tests**: End-to-End CLI-Tests

### Fixtures

Zentrale Fixtures in `tests/conftest.py`:
- `temp_dir`: Temporäres Verzeichnis
- `sample_config`: Beispiel-Config
- `sample_command`: Beispiel-Command

## Build

### Package bauen

```bash
python -m build
```

### Distribution erstellen

```bash
python -m build --wheel
python -m build --sdist
```

## CI/CD

Das Projekt verwendet GitHub Actions für CI/CD:

- **Test**: Multi-OS (Ubuntu, Windows, macOS) × Multi-Python (3.11, 3.12, 3.13)
- **Lint**: Ruff + Mypy
- **Build**: Package-Build und Validierung
- **Coverage**: Upload zu Codecov

Siehe [.github/workflows/ci.yml](https://github.com/yourusername/sindri/blob/main/.github/workflows/ci.yml) für Details.

## Contributing

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Mache deine Änderungen
4. Füge Tests hinzu
5. Stelle sicher, dass alle Tests bestehen
6. Erstelle einen Pull Request

Siehe [Contributing Guide](contributing.md) für Details.

## Code-Review-Kriterien

- ✅ Tests hinzugefügt/aktualisiert
- ✅ Code-Stil eingehalten
- ✅ Type Hints vorhanden
- ✅ Docstrings für öffentliche APIs
- ✅ Keine Breaking Changes (oder dokumentiert)

## Release-Prozess

1. Version in `pyproject.toml` erhöhen
2. Changelog aktualisieren
3. Tag erstellen: `git tag v0.1.5`
4. Push Tag: `git push origin v0.1.5`
5. GitHub Actions erstellt automatisch Release

