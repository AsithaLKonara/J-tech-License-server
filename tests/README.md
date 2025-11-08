## Automated Test Plan Summary

This directory houses automated coverage for the shared dimension scoring pipeline and parser integrations.

### Structure

| File | Purpose |
|------|---------|
| `helpers.py` | Utility functions for generating synthetic RGB payloads |
| `test_dimension_scorer.py` | Unit coverage for factorization, scoring, frame inference |
| `test_parser_consistency.py` | Ensures all parsers agree on inferred metadata |
| `test_fixture_regressions.py` | Regression suite against known layout fixtures |
| `test_ui_preview.py` | Validates confidence propagation to UI preview warnings |
| `test_scaling.py` | Performance baseline for large payloads (`pytest -m slow`) |

### Running Tests

```bash
pytest
pytest -k scorer           # dimension scorer focused
pytest -m slow             # performance benchmarks
```

### Notes

- Keep fixtures in `tests/fixtures/` synchronized with real hardware patterns.
- Update `docs/DIMENSION_SCORER_DESIGN.md` whenever scoring heuristics change.
- Run `pytest --cov` in CI to track coverage for `core/dimension_scorer.py` and parsers.

