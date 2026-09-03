# FMS

FMS groups market-data work into two projects:

- [Alpaca](Alpaca/README.md): Alpaca connection checks and market-data notebooks.
- [Simulated Engine](Simulated%20Engine/README.md): the deterministic Python/FastAPI market-data simulator, dashboard, tests, migrations, and roadmap.

```text
FMS/
    Alpaca/
        README.md
        notebooks/
    Simulated Engine/
        README.md
        AGENTS.md
        pyproject.toml
        Docs/
        app/
        migrations/
        notebooks/
        tests/
    AGENTS.md
    README.md
    .env.example
    .gitignore
```

Each project owns its documentation and source files. Alpaca currently contains a connection notebook; add its `Docs/` and `app/` folders when needed.

## Local setup

Run these commands from the repository root. The existing root `.venv` remains a shared local environment; Alpaca credentials remain in the root `.env.local`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e "./Simulated Engine[dev]"
cd "Simulated Engine"
python -m uvicorn app.main:app --reload
```

Open the dashboard at <http://127.0.0.1:8000/>. To run simulator tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest "Simulated Engine/tests"
```

If dependencies were installed before the folder move, rerun the editable install above to refresh the package location.
