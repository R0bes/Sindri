<div align="center">

<img src="assets/logo.png" alt="Sindri Logo" width="200">

# Sindri

**A project-configurable command palette for common dev workflows**

</div>

Sindri bietet eine interaktive TUI (Text User Interface) und CLI zur Verwaltung von projektspezifischen Commands, wodurch es einfach wird, Setup-, Build-, Test- und Deployment-Aufgaben auszuführen.

## 🚀 Quick Start

```bash
# Installation
pip install sindri-dev

# Projekt initialisieren
sindri init

# Interaktive TUI öffnen
sindri

# Command direkt ausführen
sindri run setup
```

## ✨ Features

- 🎯 **Interactive TUI**: Schöne Terminal-Oberfläche mit Suche, Filterung und Command-Details
- 📝 **Project-Specific Config**: Jedes Repository definiert seine eigenen Commands via `sindri.toml`
- 🚀 **Async Execution**: Commands asynchron mit Live-Output-Streaming ausführen
- 🔄 **Parallel Execution**: Mehrere Commands gleichzeitig ausführen
- 📊 **Multi-Stream Logs**: Logs von mehreren Commands in Split-Panes anzeigen
- ⚙️ **Rich Configuration**: Unterstützung für Dependencies, Timeouts, Retries, Watch Mode und mehr
- 🐳 **Docker Support**: Built-in Unterstützung für Docker und Docker Compose Workflows

## 📚 Dokumentation

### Für Benutzer

- **[Getting Started](getting-started.md)** - Installation und erste Schritte
- **[Konfiguration](configuration.md)** - Detaillierte Konfigurationsoptionen
- **[CLI Referenz](cli-reference.md)** - Alle CLI-Befehle im Detail
- **[Recipes](recipes.md)** - Praktische Beispiele für verschiedene Use Cases

### Für Entwickler

- **[Architektur](architecture.md)** - Systemarchitektur und Design-Entscheidungen
- **[Development Guide](development.md)** - Setup und Entwicklungsumgebung
- **[API Referenz](api-reference.md)** - API-Dokumentation für Entwickler
- **[Testing](testing.md)** - Test-Strategie und Coverage

## 🏗️ Architektur

Sindri folgt einer klaren 4-Schichten-Architektur:

1. **CLI Layer**: Typer-basiertes Interface
2. **Core Layer**: Registry, Execution, Templates
3. **Groups Layer**: Built-in Command Groups
4. **Config Layer**: TOML-basierte Konfiguration

Siehe [Architektur-Dokumentation](architecture.md) für Details.

## 📊 Projekt-Status

- ✅ **Version**: 0.1.4
- ✅ **Tests**: 195+ Tests
- ✅ **Coverage**: ~85% (CLI: 83.35%)
- ✅ **Status**: Produktionsreif

Siehe [Projektanalyse](analysis.md) für eine detaillierte Bewertung.

## 🤝 Beitragen

Beiträge sind willkommen! Siehe [Contributing Guide](contributing.md) für Details.

## 📄 Lizenz

MIT License - siehe [LICENSE](../LICENSE) Datei für Details.

## 🙏 Danksagungen

- Erstellt mit [Textual](https://github.com/Textualize/textual) für die TUI
- Verwendet [Typer](https://github.com/tiangolo/typer) für die CLI
- Konfiguration powered by [Pydantic](https://github.com/pydantic/pydantic)

---

**Letzte Aktualisierung:** 2025-01-12

