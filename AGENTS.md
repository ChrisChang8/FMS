# Agent Notes

This repository contains two market-data projects:

- `Alpaca/`: Alpaca connectivity notebooks. Start with `Alpaca/README.md`.
- `Simulated Engine/`: the local Python/FastAPI simulator. Read `Simulated Engine/AGENTS.md`, `Simulated Engine/README.md`, and `Simulated Engine/Docs/DATA_ROADMAP.md` before simulator changes.

Use `rg --files` to inspect the current structure. Keep source, tests, notebooks, migrations, and documentation within their owning project. Preserve existing user changes and avoid unrelated generated files or broad refactors.

Simulator phases 1–11 are implemented. Phase 12 has schema scaffolding and a design note only. Do not begin Phase 12 unless explicitly requested.

The root `.venv` is a shared local environment. Root `.env.local` / `env.local` contains Alpaca credentials; do not commit secrets or notebook outputs containing sensitive data.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -e "./Simulated Engine[dev]"
.\.venv\Scripts\python.exe -m pytest "Simulated Engine/tests"
```

Run the simulator from its project directory:

```powershell
cd "Simulated Engine"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
