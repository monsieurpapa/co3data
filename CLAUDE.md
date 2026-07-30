# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this actually is

CO3DATA's **target product** is a coffee/cocoa cooperative management system for DRC (Goma/Great Lakes region) — the workspace-wide DRC focus and French-first UI from the top-level `CLAUDE.md` apply here. That DRC/coffee/cocoa version is being newly designed; it does not exist in the code yet.

What exists in the repo today is two prior, unrelated projects layered on top of each other:

1. **Structural/stack template**: the Django project layout, `Makefile`, `docker-compose.yml`, and most of `docs/*.md` were copied from an earlier, unrelated "accounting_project" (double-entry bookkeeping, SYSCOHADA). Those docs describe apps (`accounting`, `budget`, `cashflow`, `assets`, `reporting`) that **do not exist in this codebase** — don't trust them for architecture facts.
2. **Domain model content**: the actual models (`src/cooperatives`, `src/users`, `src/sync`, etc.) were written for a *different* engagement — SACCO cooperatives in **Eswatini** under a DGRV/MCIT government TOR ("SUCOSA II"). Role names, the `Region` model, financial models (`LoanAccount`, `SavingsAccount`, `SACCOFinancialSummary`), and cooperative types all reflect Eswatini SACCOs, not DRC coffee/cocoa farming cooperatives.

**Current direction**: use the Eswatini TOR build as a reference for *what a solid cooperative-management TOR/spec looks like* (roles, audit trails, KPIs, offline sync, 2FA), but redesign the domain layer for DRC coffee/cocoa cooperatives — production/harvest tracking, farms/plots, quality grading, certifications (Fairtrade/Organic/Rainforest Alliance), pricing and sales to exporters, cooperative unions — rather than SACCO savings/lending. This is an active redesign; expect this section and the app table below to go stale fast during that work — trust `src/config/settings.py` `INSTALLED_APPS` and the app directories over any doc, including this one, when in doubt.

## Commands

The Django project root is `src/` (i.e. `src/manage.py`), while `Makefile`, `requirements.txt`, `docker-compose.yml`, `.env` live at the repo root. Run `make` targets from the repo root.

```bash
make venv             # create .venv
make install           # pip install -r requirements.txt
make migrate            # python src/manage.py migrate
make createsuperuser
make run                # runs on 0.0.0.0:8000
make test                # python src/manage.py test
make lint                # flake8 src/
make shell               # python src/manage.py shell
make clean               # remove __pycache__ / *.pyc
```

Run a single app's tests or a single test case directly (bypassing `make`):

```bash
python src/manage.py test cooperatives
python src/manage.py test cooperatives.tests.SomeTestCase.test_something
```

Only `src/users/tests.py` and `src/organization/tests.py` currently have any test content — most apps (`cooperatives`, `questionnaires`, `analytics`, `sync`) have no tests yet.

Docker (Postgres + Redis + Django/Gunicorn + Celery worker/beat + HAProxy + Nginx):

```bash
docker-compose up --build
```

Note the compose `app` service runs `gunicorn` by default; swap in `python src/manage.py runserver 0.0.0.0:8000` (commented out in `docker-compose.yml`) for local dev with autoreload.

## Architecture

**Django apps** (see `src/config/settings.py` `INSTALLED_APPS` for the authoritative list):

| App | Responsibility |
|---|---|
| `core` | Shared, cross-app models/mixins: `Attachment` (generic file uploads), `AuditLog`, `SyncLog`; `RegionalAccessMixin`, `RoleRequiredMixin`, `RegionalFormMixin` (in `core/mixins.py`); Celery tasks in `core/tasks.py` |
| `users` | Custom `User` (AbstractUser + `role`, `region`, 2FA flags, inclusion-tracking fields) and `Region`; app-level `AuditLog` (separate from `core.AuditLog`) |
| `cooperatives` | `Cooperative`, `Member`, `BoardMember`, `TrainingRecord`, `SACCOFinancialSummary`, `SavingsAccount`, `LoanAccount` — the core domain models. Has both Django views (`views.py`) and a DRF `api.py`/`serializers.py` |
| `questionnaires` | Dynamic survey engine: `Questionnaire` → `Question` → `Submission`/`Answer`. `Submission` attaches to any model via `GenericForeignKey` (cooperative, member, user, etc. per `Questionnaire.target_model`) |
| `analytics` | `KPI`, `BenchmarkThreshold`, `ReportConfiguration`, `ExportJob`, `DataValidationRule`, `DataQualityAlert` |
| `sync` | Offline mobile sync: `Device`, `PendingChange` (queued offline edits, generic FK to any model), `SyncConflict`, `SyncLog` |
| `organization` | `Organization` model exists (multi-tenant "org" concept) but is **not wired into `urls.py`** and not referenced by `cooperatives`/`users`. Treat as inactive/unused unless you're the one wiring it up |

**Access control is region-based, not organization-based**, despite the `organization` app's existence: `core.mixins.RegionalAccessMixin` filters querysets by `request.user.region`, and `RoleRequiredMixin` restricts views by `User.role` (`system_admin`, `government`, `apex_body`, `regional_officer`, `sacco_manager`, `field_agent`, `member`, `auditor`). Superusers bypass both checks.

**Generic relations pattern**: several models use `ContentType` + `GenericForeignKey` to attach to arbitrary target models — `core.Attachment`, `core.AuditLog`, `questionnaires.Submission`, `sync.PendingChange`. When adding a new model that should support file attachments, questionnaire submissions, or offline sync, this is the existing extension point rather than adding FK fields per-model.

**URL routing** (`src/config/urls.py`): uses `i18n_patterns` with `prefix_default_language=False`, so most app URLs have no language prefix in the default language. `analytics.urls` is mounted at `/` (root), `cooperatives.urls` at `/cooperatives/`, `users.urls` at `/users/`, `questionnaires.urls` at `/questionnaires/`. JWT (`djangorestframework-simplejwt`) endpoints and `sync.urls` (device registration, push/pull, conflict resolution) live outside `i18n_patterns` under `/api/`.

**i18n**: `LANGUAGE_CODE` defaults to `fr`, with `LANGUAGES = [fr, sw, en]` at the Django site level — but `User.preferred_language` (in `users/models.py`) uses a *different* set (`en`, `ss` SiSwati, `pt` Portuguese), left over from the Eswatini adaptation. These two language lists are inconsistent; don't assume one implies the other.

**Storage/auth**: Cloudinary is used for media storage when `CLOUDINARY_URL` is set (falls back to local `MEDIA_ROOT` otherwise). Auth is `django-allauth` (email + Google OAuth) plus JWT for API/mobile clients; `django-axes` provides brute-force protection; `django-otp`/`two_factor` are installed for 2FA (`User.requires_2fa` gates roles that must enroll) though the `two_factor` URL include is currently commented out in `config/urls.py`.

**Background jobs**: Celery tasks live in `core/tasks.py` (KPI computation per cooperative, data quality checks, sync log cleanup) and are scheduled via `django-celery-beat`. Note several tasks contain stale/no-op logic from a prior model refactor (e.g. `compute_kpis_for_cooperative` and `run_data_quality_checks` have comments noting the underlying logic needs to be reconnected to `SACCOFinancialSummary`/`ValidationService`) — check before assuming these are fully implemented.
