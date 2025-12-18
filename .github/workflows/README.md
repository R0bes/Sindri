# GitHub Actions Workflows

Dieses Verzeichnis enthält GitHub Actions Workflows für CI/CD.

## Workflows

### 1. CI (`ci.yml`)

Führt Tests und Linting bei jedem Push und Pull Request aus.

**Trigger:**
- Push auf `main` oder `master`
- Pull Requests gegen `main` oder `master`

**Jobs:**
- **Test**: Führt Tests auf mehreren Python-Versionen (3.11, 3.12, 3.13) und Betriebssystemen (Ubuntu, Windows, macOS) aus
- **Lint**: Führt Code-Qualitätsprüfungen mit `ruff` und `mypy` aus
- **Build**: Baut das Package und prüft es mit `twine check`

### 2. Release (`release.yml`)

Baut und veröffentlicht das Package zu PyPI bei neuen Version-Tags.

**Trigger:**
- Push von Tags im Format `v*.*.*` (z.B. `v0.1.0`, `v1.2.3`)
- Manueller Workflow-Dispatch mit Versionsangabe

**Schritte:**
1. Extrahiert die Version aus dem Tag oder Input
2. Verifiziert, dass die Version in `pyproject.toml` übereinstimmt
3. Baut das Package
4. Prüft das Package mit `twine check`
5. Veröffentlicht zu PyPI (verwendet Trusted Publishing, kein Secret nötig)
6. Erstellt ein GitHub Release (bei Tag-Push)

**Erforderliche Setup:**
- PyPI Trusted Publishing muss für dieses GitHub Repository konfiguriert sein
- Siehe: https://docs.pypi.org/trusted-publishers/

### 3. Auto Version Bump (`version-bump.yml`)

Erstellt automatisch einen Version-Tag, wenn die Version in `pyproject.toml` geändert wurde.

**Trigger:**
- Push auf `main` oder `master` mit Änderungen an `pyproject.toml`

**Schritte:**
1. Liest die aktuelle Version aus `pyproject.toml`
2. Prüft, ob ein Tag für diese Version bereits existiert
3. Erstellt und pusht einen neuen Tag im Format `v<VERSION>`, falls noch nicht vorhanden

**Hinweis:** Dieser Workflow wird übersprungen, wenn der Commit-Message `[skip version]` enthält.

## Setup

### 1. PyPI Trusted Publishing konfigurieren

1. Gehe zu [pypi.org](https://pypi.org) und logge dich ein
2. Gehe zu deinem Projekt → Settings → Trusted publishers
3. Klicke auf "Add" → "Add a new trusted publisher"
4. Wähle "GitHub Actions" als Publisher
5. Gib dein GitHub Repository ein (z.B. `R0bes/sindri`)
6. Workflow filename: `.github/workflows/release.yml`
7. Speichere die Konfiguration

**Hinweis:** Trusted Publishing ist sicherer als API Tokens, da keine Secrets gespeichert werden müssen.

### 3. Workflow Permissions

Die Workflows benötigen folgende Permissions:
- `contents: read` (Standard)
- `contents: write` (für Auto Version Bump)
- `id-token: write` (für PyPI Trusted Publishing, optional)

Diese werden automatisch durch die `permissions`-Sektionen in den Workflows gesetzt.

## Verwendung

### Manuelle Version veröffentlichen

1. Aktualisiere die Version in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. Committe und pushe die Änderung:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git push
   ```

3. Der Auto Version Bump Workflow erstellt automatisch einen Tag `v0.2.0`

4. Der Release Workflow wird durch den Tag getriggert und veröffentlicht zu PyPI

### Manueller Release über GitHub Actions

1. Gehe zu Actions → Release
2. Klicke auf "Run workflow"
3. Gib die Version ein (z.B. `0.2.0`)
4. Klicke auf "Run workflow"

### Version Bump überspringen

Wenn du eine Änderung an `pyproject.toml` machst, aber keinen Tag erstellen möchtest:

```bash
git commit -m "Update dependencies [skip version]"
```

## Troubleshooting

### Workflow schlägt fehl

- Prüfe, ob `PYPI_API_TOKEN` korrekt gesetzt ist
- Prüfe, ob die Version in `pyproject.toml` dem Tag-Format entspricht
- Prüfe die Workflow-Logs in GitHub Actions

### Tag wird nicht erstellt

- Prüfe, ob der Commit `[skip version]` enthält
- Prüfe, ob der Tag bereits existiert
- Prüfe die Workflow-Permissions

### PyPI Upload schlägt fehl

- Prüfe, ob PyPI Trusted Publishing korrekt konfiguriert ist
- Prüfe, ob das Repository und Workflow-Filename in PyPI übereinstimmen
- Prüfe, ob die Version bereits auf PyPI existiert (Versionen können nicht überschrieben werden)
- Prüfe, ob das Package korrekt gebaut wurde

