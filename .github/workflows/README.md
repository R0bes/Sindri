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
5. Veröffentlicht zu PyPI (benötigt `PYPI_API_TOKEN` Secret)
6. Erstellt ein GitHub Release (bei Tag-Push)

**Erforderliche Secrets:**
- `PYPI_API_TOKEN`: PyPI API Token für die Veröffentlichung

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

### 1. PyPI API Token erstellen

1. Gehe zu [pypi.org](https://pypi.org) und logge dich ein
2. Gehe zu Account Settings → API tokens
3. Erstelle einen neuen API Token (Scope: "Entire account" oder nur für dieses Projekt)
4. Kopiere den Token

### 2. GitHub Secret hinzufügen

1. Gehe zu deinem GitHub Repository
2. Settings → Secrets and variables → Actions
3. Klicke auf "New repository secret"
4. Name: `PYPI_API_TOKEN`
5. Value: Dein PyPI API Token
6. Klicke auf "Add secret"

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

- Prüfe, ob der API Token gültig ist
- Prüfe, ob die Version bereits auf PyPI existiert (Versionen können nicht überschrieben werden)
- Prüfe, ob das Package korrekt gebaut wurde

