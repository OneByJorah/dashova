# INTENT.md — MSP Admin Dashboard

> **J1-PIPELINE Phase -1 (ORACLE)** — Read-only intent reconstruction
> Generated: 2026-07-05 (verified against code state)
> Repository: `OneByJorah/dashova`
> Status: Intent Reconstructed (verified, minor corrections applied)

---

## What This System Does

**MSP Admin Dashboard** is a self-hosted IT operations control plane for Managed Service Providers. It aggregates authentication events, service health signals, staff records, and adapter-driven integrations into a single, self-contained observability surface.

### Technical Role

- **Auth Event Aggregation** — Ingests login events from multiple MSP-managed services (email, ticketing, password reset, SSO) into a centralized time-series store via a single `/ingest/service-login` POST endpoint.
- **Staff & Service Registry** — Tracks staff identities (name, email, Telegram ID) and service definitions, auto-creating records on first event. Staff and Service models are auto-created if they don't exist at ingestion time.
- **Admin Visibility** — A lightweight single-page admin UI (`admin/index.html`) displays recent login activity (time, staff, service, event type, source IP) fetched from the API's `/admin/events` endpoint.
- **Adapter Layer** — Pluggable integration adapters that push events from external systems (email IMAP/SMTP, osTicket API, password-reset workflows) into the ingestion endpoint. Adapters are standalone Python scripts, not plugins loaded by the API.
- **Self-Hosted Stack** — FastAPI backend + TimescaleDB (time-series PostgreSQL) + Nginx placeholder, all orchestrated via Docker Compose. No external SaaS dependencies.

### Operational Role

Serves as the **centralized observability pane** for an MSP's multi-tenant operations. Rather than logging into each client's system individually to check who authenticated, the dashboard collects auth events from every integrated service and presents them in one place. The adapter layer makes it extensible to any system that can emit a login event.

---

## Why This Was Built

### The Real Problem

Managed Service Providers (MSPs) operate dozens — sometimes hundreds — of client environments. Each client has its own email system, ticketing platform, password management, VPN, and line-of-business applications. When an MSP technician needs to answer "who logged into what, and when," they face:

1. **Fragmented visibility** — No single pane for auth events across client systems.
2. **SaaS lock-in** — Commercial SIEM/SOAR tools are expensive, complex, and often require sending sensitive auth data to third-party cloud infrastructure.
3. **Compliance overhead** — MSPs handling HIPAA, SOC 2, or GDPR data need to retain and review access logs without exposing them to external vendors.
4. **No lightweight option** — Existing self-hosted options (Splunk, Wazuh, Graylog) are heavy, log-oriented, and not purpose-built for auth-event aggregation at MSP scale.

### Why Existing Tools Were Insufficient

| Tool | Problem |
| ------ | --------- |
| Commercial SIEM (Splunk, Sumo Logic) | Expensive, SaaS-dependent, overkill for auth-only use case |
| Open-source log managers (Graylog, Loki) | General-purpose log ingestion, not auth-event shaped; heavy infrastructure |
| Built-in platform audit logs | Per-system, no aggregation; requires logging into each client environment |
| Self-hosted SIEM (Wazuh, Security Onion) | Complex deployment, agent-based, full IDS/IPS feature set not needed here |

### What Triggered Development

The need for a **zero-friction, self-hosted auth observability tool** that an MSP can deploy in 60 seconds (`docker compose up -d`) and immediately start receiving auth events from its adapters. The project was triggered by the operational reality that MSP technicians spend disproportionate time cross-referencing login logs across disparate client systems — a problem that a purpose-built, lightweight aggregator solves directly.

### JorahOne Ecosystem Fit

This is a foundational **Observability** component in the JorahOne portfolio of self-hosted MSP infrastructure tools. It pairs with:

- Other JorahOne self-hosted tools that emit auth events consumable by the adapter layer
- The broader JorahOne philosophy: **enterprise-grade, self-hosted, no SaaS lock-in, deployable in minutes**

```text
JorahOne Ecosystem
├── dashova                ← Auth event observability & aggregation
├── [other MSP tools]      ← Emit auth events consumed by adapters
└── [Hermes Agent]         ← Orchestration & pipeline layer
```

---

## Operational Classification

| Dimension | Classification |
| ----------- | --------------- |
| **Primary** | **Observability** — Auth event aggregation, service health monitoring, staff activity tracking |
| **Secondary** | **Automation** — Adapter layer programmatically ingests events from external systems |
| **Tertiary** | **Security** — Auth event audit trail supports security review and incident response |
| **Not** | Production workload scheduler, CI/CD pipeline, data pipeline, or end-user application |

**Classification rationale:** The system's core value is *seeing* what happened across services (Observability). The adapter layer automates the ingestion (Automation). The resulting audit trail supports security use cases (Security). It is not a production-critical workload scheduler or a user-facing SaaS product.

---

## Key Architectural Decisions (Reconstructed)

1. **TimescaleDB over plain PostgreSQL** — Time-series optimization for auth events queried by time range; automatic partitioning via hypertables. However, the current `app.py` uses standard SQLAlchemy models without TimescaleDB-specific features (no hypertable creation, no time-series optimizations in the schema). The TimescaleDB image is used but the application doesn't leverage its hypertable capabilities yet.

2. **FastAPI over Flask/Django** — Async-first, modern Python, automatic OpenAPI docs, lightweight for a focused API surface.

3. **Single-file backend** — `api/app.py` contains models, routes, and DB setup in one file. Trade-off: simplicity over modularity at this stage.

4. **Adapter pattern** — External systems push events via HTTP to a single ingestion endpoint. Adapters are standalone scripts, not plugins loaded by the API. This keeps the API decoupled from integration logic. Two of three adapters (email, password-reset) have functional `post()` implementations; the osTicket adapter is a skeleton with docstring and config only.

5. **Nginx placeholder (not production)** — The compose file uses `nginxdemos/hello:latest` as a placeholder, not a real reverse proxy. No Nginx config is mounted, no TLS termination is configured, and the admin UI is not served through it. This is an aspirational architecture point, not current reality.

6. **No authentication on the admin UI** — The current admin page fetches from the API directly (`http://localhost:42000`) with no auth. Intended for internal/admin networks, not public exposure. The admin UI also hardcodes the API URL to `localhost:42000`, which will not work when accessed from a different host.

---

## Current State (v1.0.0 — aspirational, no git tag)

- **Working:** FastAPI backend with SQLAlchemy models, ingestion endpoint (`POST /ingest/service-login`), event listing endpoint (`GET /admin/events`), health check (`GET /health`)
- **Working:** Docker Compose orchestration (API + TimescaleDB + Nginx hello placeholder)
- **Working:** Email and password-reset adapters (functional `post()` implementations)
- **Skeleton:** osTicket adapter (docstring + config only, no implementation)
- **Skeleton:** Admin UI (single HTML page, fetches from API, no auth, hardcoded localhost URL)
- **Missing:** Tests, CI/CD pipeline (no `.github/` directory), structured logging, rate limiting, admin authentication, production Nginx config, git tags
- **Bug:** The `/admin/events` endpoint returns `service_id` (integer FK) instead of the service name, but the admin UI displays it as a service name — the UI will show numeric IDs

---

## Repository Structure

```text
dashova/
├── adapters/                  # Integration adapters (standalone Python scripts)
│   ├── email/adapter.py       #   Functional: pushes email login events
│   ├── osticket/adapter.py    #   Skeleton: docstring + config only
│   └── password-reset/adapter.py  # Functional: pushes password-reset events
├── admin/
│   └── index.html             # Single-page admin UI (no auth, hardcoded localhost)
├── api/
│   ├── app.py                 # FastAPI backend (models, routes, DB — single file)
│   ├── Dockerfile             # Python 3.11-slim, uvicorn
│   └── requirements.txt       # fastapi, uvicorn, sqlalchemy, psycopg, httpx, etc.
├── docker-compose.yml         # 3 services: dashboard (nginx hello), api, timescaledb
├── compose.env.example        # Environment template (has a malformed line)
├── CHANGELOG.md               # v1.0.0 entry
├── README.md                  # Project README with badges, features, quick start
├── ROADMAP.md                 # Brief roadmap (production stability, docs, tests)
├── SECURITY.md                # Security policy (48h response, 90-day disclosure)
├── CONTRIBUTING.md            # Contribution guidelines
├── CODE_OF_CONDUCT.md         # Contributor Covenant v2.1
├── LICENSE                    # MIT
├── INTENT.md                  # This file
└── .gitignore                 # .env, .git, .github, __pycache__, *.log
```

---

## Notes

- **Nginx is a placeholder, not a reverse proxy**: The `dashboard` service uses `nginxdemos/hello:latest` — a demo container that shows a "hello" page. No Nginx config is mounted, no TLS is configured, and the admin UI is not served through it. The INTENT.md previously described this as "production-grade serving" — this is aspirational, not current reality.
- **No `.github/` directory**: Despite a commit message "ci: add deploy manifest for MSP Admin Dashboard" (53d0028), no `.github/` directory exists in the current tree. The deploy manifest may have been removed or the commit was reverted. No CI/CD workflows, issue templates, or Dependabot config exist.
- **No git tags**: CHANGELOG.md claims v1.0.0 but no git tag exists. The version is aspirational.
- **`compose.env.example` has a malformed line**: Line 5 reads `DATABASE_URL=postgresql://msp:******* DASHBOARD_PORT=3000` — `DASHBOARD_PORT` is concatenated on the same line without a newline, making it part of the DATABASE_URL value. This is a config file defect.
- **Admin UI hardcodes `http://localhost:42000`**: The admin page fetches from a hardcoded localhost URL. This won't work when accessed from a different machine or behind a reverse proxy.
- **`/admin/events` returns `service_id` (integer) not service name**: The API returns `r.service_id` (an integer foreign key) but the admin UI displays it as `row.service`. The UI will show numeric IDs instead of service names — this is a bug.
- **TimescaleDB not leveraged in code**: The compose uses `timescale/timescaledb:latest-pg16` but `app.py` uses standard SQLAlchemy models without hypertable creation or any TimescaleDB-specific features. The time-series capability is available but unused.
- **Security audit in git history**: Commit `8458529` ("audit(dashova): sanitize email references") indicates a prior security review — a positive maturity signal.
- **Dependabot activity**: Two dependency bumps in git history (`python-multipart` 0.0.9→0.0.31, `python-dotenv` 1.0.1→1.2.2) suggest Dependabot was configured at some point, but no `.github/dependabot.yml` exists currently.
- **No health checks**: The compose file defines no health checks for any service.
- **No tests directory**: No `tests/` directory or test files exist anywhere in the repo.
