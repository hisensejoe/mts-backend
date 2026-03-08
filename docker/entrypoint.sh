#!/usr/bin/env bash
set -euo pipefail

python -m app.scripts.wait_for_db
alembic upgrade head

exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
