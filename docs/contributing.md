# Contributing Guide

Vielen Dank für Ihr Interesse, zu Sindri beizutragen! Dieser Guide hilft Ihnen beim Einstieg.

## Code of Conduct

Bitte seien Sie respektvoll und konstruktiv in allen Interaktionen.

## Wie kann ich beitragen?

### Bug Reports

Wenn Sie einen Bug gefunden haben:

1. Prüfen Sie, ob der Bug bereits gemeldet wurde
2. Erstellen Sie ein Issue mit:
   - Klarer Beschreibung des Problems
   - Schritten zur Reproduktion
   - Erwartetem vs. tatsächlichem Verhalten
   - Umgebung (OS, Python-Version)

### Feature Requests

Für neue Features:

1. Prüfen Sie, ob das Feature bereits vorgeschlagen wurde
2. Erstellen Sie ein Issue mit:
   - Beschreibung des Features
   - Use Case / Motivation
   - Mögliche Implementierung (wenn vorhanden)

### Pull Requests

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Machen Sie Ihre Änderungen
4. Fügen Sie Tests hinzu
5. Stellen Sie sicher, dass alle Tests bestehen (`pytest`)
6. Committen Sie Ihre Änderungen (`git commit -m 'Add amazing feature'`)
7. Pushen Sie zum Branch (`git push origin feature/amazing-feature`)
8. Öffnen Sie einen Pull Request

## Development Setup

Siehe [Development Guide](development.md) für Details zum Setup.

## Code-Standards

### Python Style

- **Linting**: Ruff
- **Formatting**: Ruff (Black-kompatibel)
- **Type Hints**: Umfassend verwenden
- **Docstrings**: Google-Style für öffentliche APIs

### Commit Messages

Verwenden Sie klare, beschreibende Commit-Messages:

```
feat: Add support for custom command groups
fix: Fix config discovery in nested directories
docs: Update CLI reference documentation
test: Add tests for subcommands module
refactor: Simplify command parsing logic
```

### Tests

- Alle neuen Features müssen Tests haben
- Tests müssen bestehen (`pytest`)
- Coverage sollte nicht sinken
- Ziel: 90%+ Coverage

## Pull Request Prozess

1. **Beschreibung**: Klare Beschreibung der Änderungen
2. **Tests**: Alle Tests müssen bestehen
3. **Coverage**: Coverage sollte nicht sinken
4. **Dokumentation**: Relevante Dokumentation aktualisieren
5. **Code Review**: Warten auf Review und Feedback

## Code Review Kriterien

- ✅ Code-Stil eingehalten
- ✅ Tests hinzugefügt/aktualisiert
- ✅ Type Hints vorhanden
- ✅ Docstrings für öffentliche APIs
- ✅ Keine Breaking Changes (oder dokumentiert)
- ✅ Dokumentation aktualisiert

## Fragen?

Fühlen Sie sich frei, ein Issue zu erstellen oder eine Discussion zu starten!

---

**Vielen Dank für Ihre Beiträge!** 🎉

