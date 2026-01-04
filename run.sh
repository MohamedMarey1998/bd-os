#!/usr/bin/env bash
set -e
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BDOS_SECRET_KEY="dev_secret_change_me"
uvicorn app.main:app --reload --port 8000
