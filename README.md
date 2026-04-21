# Pool Tournament Draw & Score Tracker (PostgreSQL)

This repository now contains a starter implementation for a **Pool Tournament Draw + Live Score Tracking** platform inspired by the flow you described.

## What this build includes

### Public Player-Facing Features
- Search tournaments by name/location.
- List only tournaments that are:
  - `scheduled` or `running`, and
  - have **draw published**.
- View a tournament detail page with match cards/scores and live/finished status.

### Admin Panel Features
- Admin authentication (session-based login).
- Create tournaments.
- Manage tournament settings:
  - status (`scheduled`, `running`, `completed`)
  - toggle draw published
- Add players to a tournament.
- Create draw/matches manually.
- Update match scores and set match finished status.

## Tech Stack
- **FastAPI** (backend + server-rendered web app)
- **PostgreSQL** via SQLAlchemy + psycopg
- **Jinja2** templates for UI

## Quick Start

1. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables:

```bash
export DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/pool_tournaments'
export ADMIN_USERNAME='admin'
export ADMIN_PASSWORD='change-me'
export SESSION_SECRET='replace-with-a-random-secret'
```

3. Run app:

```bash
uvicorn app.main:app --reload
```

4. Visit:
- Public list: `http://127.0.0.1:8000/`
- Admin login: `http://127.0.0.1:8000/admin/login`

## Suggested next steps
- Add role-based admin users stored in DB.
- Add automatic bracket generation (single/double elimination).
- Add audit logs for score updates.
- Add websocket updates for real-time scoreboard updates.
- Add CSV import/export for players and fixtures.
