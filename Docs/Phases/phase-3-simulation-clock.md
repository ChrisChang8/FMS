# Phase 3 - Simulation Clock

Phase 3 adds a deterministic clock for the market data simulator. The clock controls simulated market time without generating prices, ticks, candles, APIs, WebSockets, or storage.

## What Phase 3 Created

Phase 3 added `app/simulation/clock.py`, which contains:

- `SimulationClock`
- `SimulationClockConfig`
- `MARKET_TIMEZONE_NAME`
- `MARKET_TIMEZONE`
- `REGULAR_SESSION_START`
- `REGULAR_SESSION_END`

The clock is exported from `app/simulation/__init__.py`, so other code can import it from `app.simulation`.

Example:

```python
from app.simulation import SimulationClock, SimulationClockConfig
```

## Files Created or Changed

Created:

- `app/simulation/clock.py`
- `tests/test_simulation_clock.py`
- `Docs/Phases/phase-3-simulation-clock.md`

Changed:

- `app/simulation/__init__.py`
- `pyproject.toml`
- `README.md`
- `AGENTS.md`

## Clock Details

`SimulationClockConfig` configures:

- `start_time`
- `speed`

Important validation:

- `start_time` must include timezone information.
- `start_time` is normalized to `America/Chicago`.
- `speed` must be greater than zero.

`SimulationClock` supports:

- Reading the current simulated time
- Reading the configured start time
- Pausing automatic progression
- Resuming automatic progression
- Resetting to the configured start time
- Manually advancing by a `timedelta`
- Changing simulation speed
- Checking whether a timestamp is inside the regular market session

## Market Hours

Phase 3 uses U.S. Central Time for simulated market timestamps:

```text
America/Chicago
```

The regular trading session is:

```text
8:30 AM to 3:00 PM Central Time
```

The session start is inclusive and the session end is exclusive. This means `8:30 AM` is active, but exactly `3:00 PM` is no longer active.

## Deterministic Time

Tests can use a manual time source instead of the computer clock. This makes the timeline predictable:

```python
clock.resume()
manual_time_source.advance(15)
```

If the clock speed is `2.0`, then 15 real seconds become 30 simulated seconds.

The clock also supports direct manual advancement:

```python
clock.advance(timedelta(minutes=5))
```

This is useful for tests because the result does not depend on real time passing.

## How To Set Up The Project

From the repository root:

```powershell
cd C:\Users\chris\Downloads\Github\FMS
```

Create a virtual environment if one does not already exist:

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

`tzdata` is included as a runtime dependency so `zoneinfo` can reliably load `America/Chicago` on Windows.

## How To Run All Tests

From the repository root, with the virtual environment activated:

```powershell
python -m pytest
```

Or run pytest directly through the local virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Expected result:

```text
22 passed
```

The exact runtime may vary. A pytest cache warning does not necessarily mean the test suite failed; the important result is that all tests pass.

## How To Run Only Phase 3 Tests

Run just the simulation clock tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_simulation_clock.py
```

Run one specific test by name:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_simulation_clock.py -k pause
```

The `-k pause` option tells pytest to run only tests with `pause` in the test name.

## How To Run The Application

Phase 3 does not add any new API endpoints. The existing health endpoint from Phase 1 should still work.

Start the app:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "FMS Market Data Simulator",
  "environment": "local"
}
```

## Beginner-Friendly Concepts

A **simulation clock** is a clock controlled by the simulator. It lets tests and future simulation engines move market time forward without relying on the exact time on your computer.

**Simulated time** is the time inside the market simulation. It can move faster than real time, pause, resume, or jump forward during tests.

**Wall time** is real elapsed time outside the simulator. The clock can use an injected time source for wall time, which keeps tests predictable.

**Simulation speed** controls how fast simulated time moves. A speed of `1.0` means one simulated second per real second. A speed of `2.0` means two simulated seconds per real second.

**Pause** freezes simulated time. **Resume** lets it move again.

**Reset** returns the clock to its configured start time and pauses it.

**America/Chicago** is the timezone used for simulated market timestamps. This keeps timestamps consistent as later phases add prices, ticks, and candles.

**Regular trading session** means the part of the day treated as normal stock market hours. In Phase 3, that is `8:30 AM` through just before `3:00 PM` Central Time.

## Design Decisions

- The clock lives in `app/simulation/` because it is simulation infrastructure, not an API or data model.
- The default start time is fixed so a default clock is deterministic.
- The clock starts paused so creating a clock does not immediately depend on elapsed real time.
- Reset returns to the configured start time and pauses the clock.
- Manual advancement is allowed while paused or running, which keeps tests simple and deterministic.
- Timestamps are normalized to `America/Chicago`.
- `tzdata` is a runtime dependency so timezone loading works consistently on Windows.
- No price simulation, tick generation, candle aggregation, API endpoints, WebSockets, or storage were added in Phase 3.

## Phase Boundary

Phase 3 is complete when simulated time can be controlled predictably, pause and resume work, reset returns to the configured start time, and regular market session checks use `America/Chicago`.

Do not begin Phase 4 until explicitly requested.
