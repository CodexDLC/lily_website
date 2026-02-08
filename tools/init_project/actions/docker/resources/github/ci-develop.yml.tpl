name: CI Develop (Linting)

on:
  push:
    branches: [ develop ]

jobs:
  lint:
    name: Fast Quality Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "{{PYTHON_VERSION}}"

      - name: Install dependencies
        run: |
          pip install ".[dev{{INSTALL_EXTRAS}}]"

      - name: Run Ruff
        run: ruff check {{LINT_PATHS}}

      - name: Run Mypy
        run: mypy {{LINT_PATHS}}
