# 🛠 Development & Validation Tools

This directory contains scripts to ensure code quality and environment consistency.

## 🚀 `check.py`
The primary quality gate for the project. It automates linting, type checking, unit testing, and Docker integration testing.

### Usage
- **Full Check**: `python tools/dev/check.py`
- **Interactive Menu**: `python tools/dev/check.py --settings`

### Features
1. **Linters**: Runs `pre-commit` hooks (trailing whitespace, ruff, etc.).
2. **Type Checking**: Full `mypy` validation with cache clearing.
3. **Unit Tests**: Executes `pytest` with local environment settings.
4. **Docker Validation**:
   - Builds images from scratch.
   - Starts the full stack.
   - Runs Django internal checks and migration validation inside the container.
   - Automatically cleans up resources.

## 🌳 `generate_project_tree.py`
Generates a visual representation of the project structure for documentation purposes.

## 🕸 `graphify_wiki.py`
Builds `graphify-out/wiki/` from the existing `graphify-out/graph.json` even when the installed `graphify` CLI does not expose a `wiki` command.

### Usage
- `powershell -ExecutionPolicy Bypass -File tools/dev/graphify_wiki.ps1`
- `python tools/dev/graphify_wiki.py .`

### What it does
1. Reuses the already generated `graphify-out/graph.json`.
2. Imports the installed `graphifyy` package directly from the local `uv` tool environment when needed.
3. Writes `graphify-out/wiki/index.md` plus one article per community and god node.
