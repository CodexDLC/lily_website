name: CI Main (Testing & Build Check)

on:
  pull_request:
    branches: [ main ]

jobs:
  tests:
    name: Full Test Suite
    runs-on: ubuntu-latest
{{SERVICES_BLOCK}}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "{{PYTHON_VERSION}}"

      - name: Install dependencies
        run: |
          pip install ".[dev{{INSTALL_EXTRAS}}]"

      - name: Run Pytest
        env:
{{TEST_ENV_VARS}}
        run: pytest

  build-check:
    name: Docker Build Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{{BUILD_STEPS}}
