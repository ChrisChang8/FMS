# FMS Notebook Guide

This folder contains Jupyter notebooks for exploring FMS simulator output in VS Code. This guide is separate from the project-level `README.md`.

## Notebook Files

### `price_engine_visualization.ipynb`

Visualizes the Phase 4 price simulation engine.

What it does:

- Imports the real `PriceSimulationEngine` from `app.simulation`.
- Simulates the default 10-stock universe.
- Renders an inline SVG chart through VS Code's Jupyter notebook renderer.
- Shows a summary table with each symbol's starting price, ending price, and percent change.

## Recommended Setup

From the repository root:

```powershell
cd C:\Users\chris\Downloads\Github\FMS
```

Create a virtual environment if needed:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project with development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Register the environment as a Jupyter kernel:

```powershell
python -m ipykernel install --user --name fms --display-name "FMS (.venv)"
```

Then open a notebook in VS Code and select the `FMS (.venv)` kernel.

## Dependencies

Runtime dependencies used by the current notebook:

- `numpy`
- `pydantic`
- `tzdata`

Notebook/Jupyter dependencies:

- `ipykernel`
- `IPython`

The easiest way to install everything is:

```powershell
python -m pip install -e ".[dev]"
```

## Understanding The Chart

The x axis is time elapsed in the simulation, measured in minutes.

The y axis is relative price movement, not the raw dollar price.

`Start = 100` means each stock begins from the same chart baseline. This makes movement shapes easy to compare. If a line moves from `100` to `101`, that stock is up about 1% from its first simulated price. If it moves from `100` to `99`, it is down about 1%.

The summary table below the chart shows the actual simulated dollar prices.

## Fixing `ZoneInfoNotFoundError`

If you see this error:

```text
ZoneInfoNotFoundError: 'No time zone found with key America/Chicago'
```

the selected notebook kernel does not have the `tzdata` package installed. This usually happens when VS Code is using a different Python interpreter than the repository `.venv`.

Fix it by selecting the `FMS (.venv)` kernel, or install `tzdata` into the currently selected kernel:

```powershell
python -m pip install tzdata
```

The first code cell in `price_engine_visualization.ipynb` also checks for missing runtime packages and installs them into the active notebook kernel before importing the simulator.

## Running A Notebook In VS Code

1. Open the `.ipynb` file.
2. Click the kernel picker in the top-right of the notebook.
3. Select `FMS (.venv)` or another environment with the dependencies installed.
4. Click `Run All`.

If the first cell prints a Python path under `.venv`, the notebook is using the intended environment.
