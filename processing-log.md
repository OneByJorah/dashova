dashova Tier 2 audit - branch repo-elevation/dashova created.
Cloned: /home/j1admin/onebyjorah-agent/repos/dashova
Secret findings: compose.env.example (SECRET_KEY=change-me, POSTGRES_PASSWORD=change-me), docker-compose.deploy.yml (SECRET_KEY: msp-dashboard-secret-key hardcoded), api/app.py (password_hash column, ForeignKey staff)
Stack: FastAPI, Python 3.11, TimescaleDB/PostgreSQL 16, Docker Compose, uvicorn, SQLAlchemy, Pydantic
Screenshot: NOT AVAILABLE (browser provider unavailable - omitted)
Errors: Browser screenshot unavailable; deploy compose has hardcoded secret.
