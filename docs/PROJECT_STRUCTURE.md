# Project Structure

This file explains the recommended and actual layout of the repository to help contributors and maintainers.

Top-level folders (recommended):

- `src/` - Core Python package code. Importable modules, algorithmic code, ML model code, and libraries.
- `backend/` - Backend services, DB models and server entry points.
- `bin/` - Convenience launchers and wrapper scripts. Copy of the most commonly-used launch scripts so users can run `bin/run_all.ps1` or `bin/run_demo.bat`.
- `tools/` - Utility scripts (data generators, repair scripts, one-off tools). These are non-critical and safe to modify.
- `deploy/` - Cloud-init templates, provisioning script, and any Terraform or infra-as-code artifacts.
- `docs/` - User-facing documentation and runbooks (QUICK_START_GUIDE, DEPLOY guides).
- `data/` - Raw session files, GeoIP DB files, and other data assets used by the demo.
- `output/` - Aggregated CSVs and export files produced by scripts and the dashboard.
- `logs/` - Runtime logs for local runs.
- `tests/` - Automated tests and test fixtures.

What I moved/copied (non-destructive):
- `bin/` now contains copies of the main launchers (`run_all.ps1`, `run_demo.*`).
- `tools/` contains copies of utility scripts (data generation, ad-hoc scripts) for discoverability.
- `docs/` contains deployment README and other documentation copies.

Notes and next steps (recommended):
1. Consider refactoring larger entry scripts into `src/` (as CLI modules) so imports work correctly and packaging is easier.
2. Optionally move root-level Python scripts into `tools/` or into `src/` depending on whether they are library code or utilities. Move only after running the test suite.
3. If you want a destructive reorg (move instead of copy), I can do that and update references — but I recommend committing current state first so moves are reversible.

If you want, I can now:
- A) Move the selected files into their new folders (destructive move) and update imports.
- B) Create stub wrapper files in root that forward/exec the relocated scripts (non-destructive).
- C) Generate a single `Makefile` or `tasks.ps1` that exposes common developer tasks (run, test, build, deploy).

Tell me which option you want and I'll implement it.
