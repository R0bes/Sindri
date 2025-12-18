<div align="center">

<img src="assets/logo.png" alt="Sindri Logo" width="200">

# Sindri

**A project-configurable command palette for common dev workflows**

</div>

Sindri ist ein modernes CLI-Tool, das eine interaktive TUI (Text User Interface) und eine leistungsstarke Kommandozeile bietet, um projektspezifische Commands zu verwalten. Es macht es einfach, Setup-, Build-, Test- und Deployment-Aufgaben auszuführen.

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

### 🎯 Interactive TUI
Schöne Terminal-Oberfläche mit Suche, Filterung und Command-Details. Navigiere durch deine Commands mit der Tastatur und sieh Live-Logs während der Ausführung.

### 📝 Project-Specific Config
Jedes Repository definiert seine eigenen Commands via `sindri.toml`. Keine globalen Konfigurationen, alles projektbezogen.

### 🚀 Async Execution
Commands werden asynchron mit Live-Output-Streaming ausgeführt. Sieh die Ausgabe in Echtzeit, während Commands laufen.

### 🔄 Parallel Execution
Führe mehrere Commands gleichzeitig aus. Perfekt für parallele Builds oder Tests.

### 📊 Multi-Stream Logs
Logs von mehreren Commands werden in Split-Panes angezeigt. Behalte den Überblick über alle laufenden Prozesse.

### ⚙️ Rich Configuration
Unterstützung für Dependencies, Timeouts, Retries, Watch Mode, Environment Variables und mehr.

### 🐳 Docker Support
Built-in Unterstützung für Docker und Docker Compose Workflows. Integrierte Commands für Build, Push, Up, Down und mehr.

### 🔧 Built-in Command Groups
Vordefinierte Command-Gruppen für Quality (test, lint, format), Git, Docker, Version Management, PyPI und mehr.

### 📚 Documentation Commands
Integrierte Commands für MkDocs: Setup, Preview, Build und Deploy.

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

1. **CLI Layer**: Typer-basiertes Interface mit Namespace-Support
2. **Core Layer**: Registry, Execution, Templates, Shell Runner
3. **Groups Layer**: Built-in Command Groups (Quality, Docker, Git, etc.)
4. **Config Layer**: TOML-basierte Konfiguration mit Discovery

Siehe [Architektur-Dokumentation](architecture.md) für Details.

## 📊 Projekt-Status

- ✅ **Version**: 0.1.4
- ✅ **Tests**: 800+ Tests
- ✅ **Coverage**: ~90% (CLI: 83.35%)
- ✅ **Status**: Produktionsreif
- ✅ **Python**: 3.11+

Siehe [Projektanalyse](analysis.md) für eine detaillierte Bewertung.

## 🤝 Beitragen

Beiträge sind willkommen! Siehe [Contributing Guide](contributing.md) für Details.

## 📄 Lizenz

MIT License - siehe [LICENSE](../LICENSE) Datei für Details.

## 🙏 Danksagungen

- Erstellt mit [Textual](https://github.com/Textualize/textual) für die TUI
- Verwendet [Typer](https://github.com/tiangolo/typer) für die CLI
- Konfiguration powered by [Pydantic](https://github.com/pydantic/pydantic)
- Dokumentation mit [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)

---

**Letzte Aktualisierung:** 2025-12-18
