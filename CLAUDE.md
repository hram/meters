# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Unified dashboard that aggregates meter readings from two sub-portals via their REST APIs and displays them in a 3-column layout (Вода / Электричество / Газ). Does not communicate with utility websites directly — all that is handled by the sibling projects `ikus.pesc.ru` (port 8003) and `peterburgregiongaz` (port 8004).

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server (use python3.10 — python3 resolves to linuxbrew 3.14 which has no packages)
uvicorn portal.main:app --reload --port 8005
python3.10 -m uvicorn portal.main:app --reload --port 8005

# Run tests
python3.10 -m pytest tests/ -v
/home/hram/projects/running-portal/.venv/bin/python3 -m pytest tests/ -v

# Trigger auto-submit manually (bypasses window gate)
curl -X POST "http://localhost:8005/api/services/trigger?force=true"
```

## Configuration

Copy `.env.example` to `.env`:
- `PESC_API_URL` — URL of the pesc portal (default `http://localhost:8003`)
- `GAZ_API_URL` — URL of the gaz portal (default `http://localhost:8004`)
- `SCHEDULER_HOUR`, `SCHEDULER_MINUTE` — auto-submit time in Moscow TZ (default 12:00)
- `DATA_DIR` — SQLite location (default `./data`)

Both sub-portals must be running before starting this portal.

## Architecture

**`src/adapters/`** — the only place that calls sub-portal APIs. Each adapter (`pesc.py`, `gaz.py`) has three responsibilities:
- `fetch()` / `fetch_split()` → returns `ServiceData` (normalized, error-safe — never raises)
- `submit_same()` → re-submits current values from sub-portal
- `submit_values(body)` → proxies custom payload verbatim to sub-portal

`PescAdapter.fetch_split()` splits the single pesc response into two `ServiceData` objects — water (`pesc_water`) and electricity (`pesc_electricity`) — by matching meter names against `_WATER_KEYWORDS`. The balance is placed on the electricity card. Water/electricity share the same `auto_submit` DB setting (`service = "pesc"`).

**`ServiceData.error`** — if a sub-portal is unreachable, `fetch()` catches the exception, populates `error`, and returns gracefully. The dashboard renders an error banner for that card without breaking other cards.

**`portal/routers/submit.py`** — routes `/api/services/{service}/submit[-values]` and `/api/submit-all`. Services `pesc_water` / `pesc_electricity` both map to the `pesc` sub-portal endpoint — the JS template handles this via `apiService(service)` which strips the suffix.

**`portal/db.py`** — two tables: `service_settings` (pre-seeded with `pesc` and `gaz` rows on `init_db()`), `scheduler_log`. No meter data is stored — all readings come live from sub-portals on each page load.

**`portal/scheduler.py`** — checks the 15–21 weekday window (Moscow time, same logic as sub-portals), then calls `adapter.submit_same()` in parallel for all enabled services. Logs each result independently so a gaz failure doesn't mask a pesc success.

## Python environment note

`python3` resolves to linuxbrew Python 3.14 (no packages installed). All project packages are under `python3.10` (`/usr/bin/python3.10`). Always use `python3.10` explicitly or `uvicorn` / `pytest` from `~/.local/bin`.
