# BD OS MVP (Internal)

Minimal internal web app to run your 12-stage Business Development service:
- Accounts (clients)
- Projects (contracts) with auto-generated 12 stages
- Stage gate: checklist + deliverables + approvals
- Tasks
- Opportunities

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# IMPORTANT: change secret key in app/config.py (or set env + edit config as desired)
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000

Default login:
- Email: admin@local
- Password: admin1234

## Notes
- SQLite DB file is created next to the code as `bd_os.db`.
- This is an MVP for internal use; harden auth + add backups before production.
