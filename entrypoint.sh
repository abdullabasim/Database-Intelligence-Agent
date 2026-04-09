#!/bin/bash
set -e

echo "--- Starting Database Migrations ---"
alembic -c app/alembic.ini upgrade head

echo "--- Running Database Seeding ---"
python -m app.seed

echo "--- Starting FastAPI Server ---"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
