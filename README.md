# SaveStack

A full-stack banking app where users deposit USD via Stripe, allocate a percentage to crypto, and view a unified cash + crypto portfolio with live BTC prices.

**Status:** in active development.

## Origin

Originated at the Capital One Tech Summit Hackathon 2026 (3rd place); expanded into a full-stack project.

## Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy 2.0 (async), Redis, Alembic
- **Frontend:** React, Vite, TypeScript, Tailwind
- **Integrations:** Stripe (test mode), Coinbase Advanced Trade WebSocket
- **Infra:** Docker Compose
- **Testing:** pytest.

## Architecture

SaveStack runs as three orchestrated services via Docker Compose:

- **PostgreSQL** — durable storage for users, accounts, deposits, and the ledger
- **Redis** — caching and pub/sub for real-time price broadcasting
- **FastAPI backend** — REST API, JWT auth, webhook handlers, WebSocket streaming

A double-entry ledger pattern is used for all financial state. Balances are derived from immutable ledger entries, with database-enforced constraints for idempotency under concurrent webhook deliveries.


## Getting started

Clone the repo and start the stack:

```bash