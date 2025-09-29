# FastAPI CRUD Booster – JetBrains Marketplace Listing

## Title & Tagline
- **Title:** FastAPI CRUD Booster for JetBrains IDEs
- **Tagline:** Scaffold production-grade FastAPI CRUD stacks directly inside your IDE.

## Short Description
- Generate a full FastAPI + React CRUD stack in minutes without leaving JetBrains IDEs.
- Pre-configured JWT auth, role-based guards, and ready-to-run API endpoints.
- Typed SQLAlchemy models, Alembic migrations, and React dashboards wired to the backend.
- Opinionated best practices for OPPO KZ Data Platform deployments on Render.com.

## Detailed Description
**Problem.** Fast-tracking OPPO KZ Data Platform features requires aligning backend, frontend, and deployment standards while avoiding repetitive boilerplate.

**Solution.** FastAPI CRUD Booster extends JetBrains IDEs with a guided wizard that assembles a FastAPI + React project following OPPO KZ conventions, so teams can focus on business logic instead of setup.

**What it generates.** The plugin scaffolds:
- FastAPI backend with versioned routers (`/api/v1`), JWT auth (access/refresh), role dependencies, feature flags, and health/version endpoints.
- PostgreSQL persistence layer using SQLAlchemy 2.0, Alembic migrations, typed Pydantic schemas, and structured logging.
- React (Vite + TypeScript + Tailwind + shadcn/ui) frontend with login/dashboard pages, axios client, and role-aware navigation.
- Render-ready deploy scripts, environment templates, and CORS configuration for Metabase integration.

**Compatibility.** Works with IntelliJ IDEA Ultimate 2022.3+, PyCharm Professional 2022.3+, and WebStorm 2022.3+. Tested on macOS 13, Windows 11, Ubuntu 22.04.

**Limitations.** Requires Java 17+, Node.js 18+, and Python 3.11+ installed locally. Does not auto-generate Metabase dashboards. Feature flags must be toggled manually via `.env`.

## Highlights
- Guided wizard for OPPO KZ-compliant domain modules (stores, sales, shipments, bonuses, coefficients).
- One-click generation of JWT auth with admin seeding (`admin@oppo.kz`).
- Automatic wiring of `/api/v1/health` and `/api/v1/version` endpoints.
- Structured logging presets and environment-aware settings management.
- Frontend scaffold with axios interceptors, Tailwind config, and shadcn/ui components.
- Render.com deployment scripts including Alembic migrate-on-start hook.
- Feature flag templates (`ENABLE_BONUSES`, `ENABLE_MESSAGES`) for phased rollout.
- Integration-ready configuration for Metabase CORS and /health probes.

## Who It’s For
Engineering teams building the OPPO KZ Data Platform, JetBrains-centric full-stack developers, and solution architects who need consistent FastAPI + React CRUD scaffolds.

## Trial & Licensing
FastAPI CRUD Booster 1.0.0 ships with a 30-day free trial. Afterward, activate via JetBrains Marketplace licensing; per-user annual subscription applies.

## Changelog 1.0.0
- Initial release with FastAPI + React full-stack scaffolding aligned to OPPO KZ guidelines.
- Added deployment templates for Render.com with environment variable guidance.
- Delivered feature flag examples and bonus/message domain toggles out of the box.
- Bundled example tests covering auth flow and health checks.

## Screenshot Captions
1. **Wizard Flow:** Configure roles, feature flags, and Render deployment variables in a guided wizard.
2. **Project Tree:** Explore the generated FastAPI + React folder structure for OPPO KZ modules.
3. **Models & Schemas:** Review typed SQLAlchemy models and matching Pydantic schemas.
4. **API Routes:** Inspect versioned routers with role-based access for stores, sales, and shipments.
5. **Automated Tests:** Run example pytest suites covering JWT login and protected endpoints.
6. **Migrations & README:** Check Alembic migration history and deployment-ready README snippets.
