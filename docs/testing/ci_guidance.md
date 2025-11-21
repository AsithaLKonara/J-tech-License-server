# CI/CD Guidance for Design Tools Testing

## Workflow Stages

1. Lint & static analysis (`ruff`, `mypy`)  
2. Unit tests (`pytest -m unit`)  
3. Integration tests (`pytest -m integration`)  
4. Property tests (`pytest -m property`) – nightly  
5. GUI tests (`pytest -m gui`) – nightly/offline  
6. Coverage report (`pytest --cov --cov-report=xml`)  
7. Upload artifacts (coverage, snapshots)

## GitHub Actions Example

```yaml
name: tests

on:
  push:
    branches: [ main ]
  pull_request:
  schedule:
    - cron: "0 3 * * *"  # nightly

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      QT_QPA_PLATFORM: offscreen
    strategy:
      fail-fast: false
      matrix:
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Unit tests
        run: pytest -m unit
      - name: Integration tests
        run: pytest -m integration
      - name: Property tests
        if: github.event_name == 'schedule'
        run: pytest -m property
      - name: GUI tests
        if: github.event_name == 'schedule'
        run: pytest -m gui
      - name: Coverage
        run: pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          fail_ci_if_error: true
```

## Additional Tips

- Cache `pip` downloads (`actions/cache`).  
- Use `pytest-xdist` for parallel unit/integration tests; keep GUI tests serial.  
- Upload failing Hypothesis examples & visual diffs as artifacts.  
- Require unit/integration checks for PR merge; treat property/GUI as advisory or gating per stability.  
- Provide local scripts mirroring CI commands (`make test-ci`).

