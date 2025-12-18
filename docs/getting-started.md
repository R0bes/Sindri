# Getting Started

Dieser Guide führt Sie durch die Installation und ersten Schritte mit Sindri.

## Installation

### Via pip

```bash
pip install sindri-dev
```

### Mit optionalen Extras

```bash
pip install sindri-dev[docker,compose,git,version,pypi]
```

### Von Source

```bash
git clone https://github.com/yourusername/sindri.git
cd sindri
pip install -e .
```

## Projekt initialisieren

Navigieren Sie zu Ihrem Projektverzeichnis und führen Sie aus:

```bash
sindri init
```

Dies erstellt eine `sindri.toml` Datei mit Beispiel-Commands. Bearbeiten Sie diese, um sie an die Bedürfnisse Ihres Projekts anzupassen.

### Interaktiver Modus

Der interaktive Modus erkennt automatisch Ihren Projekttyp und schlägt passende Command-Gruppen vor:

```bash
sindri init --interactive
```

### Non-Interactive Modus

Erstellt eine Standard-Konfiguration ohne Interaktion:

```bash
sindri init --no-interactive
```

## Erste Schritte

### Interaktive TUI öffnen

```bash
sindri
```

Die TUI bietet:
- 🔍 Suchfunktion für Commands
- 📋 Übersichtliche Command-Liste
- 📊 Live-Logs während der Ausführung
- ⌨️  Tastatur-Navigation

### Commands direkt ausführen

```bash
# Einzelner Command
sindri run setup

# Mehrere Commands parallel
sindri run start web api --parallel

# Mit Optionen
sindri run test --timeout 60 --retries 2
```

### Command-Liste anzeigen

```bash
sindri list
```

## Beispiel-Konfiguration

Eine minimale `sindri.toml` könnte so aussehen:

```toml
version = "1.0"
project_name = "my-project"

[[commands]]
id = "setup"
title = "Setup Project"
description = "Install dependencies"
shell = "pip install -r requirements.txt"

[[commands]]
id = "test"
title = "Run Tests"
description = "Execute test suite"
shell = "pytest tests/"
```

## Nächste Schritte

- Lesen Sie die [Konfigurations-Dokumentation](configuration.md) für erweiterte Features
- Schauen Sie sich die [Recipes](recipes.md) für praktische Beispiele an
- Erkunden Sie die [CLI Referenz](cli-reference.md) für alle verfügbaren Optionen

