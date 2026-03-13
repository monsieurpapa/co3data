# CO3DATA - Coffee and Cocoa Cooperatives System Database

CO3DATA is a robust, secure, and offline-capable digital ecosystem designed to centralize financial and non-financial data for cooperatives across Central Africa.

## Core Features
- **Inclusive Member Management**: Tracking production and demographic data (gender, youth).
- **Financial Monitoring**: Verifiable financial records for cooperatives and members.
- **Dynamic Questionnaires**: Customizable data collection modules.
- **Real-time Analytics**: KPI tracking and performance dashboards.
- **Offline Synchronization**: Mobile-first architecture for remote field data entry.

## Architecture
- **Backend**: Django (Python 3.12)
- **Database**: PostgreSQL
- **Task Queue**: Celery with Redis
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx & HAProxy

## Project Structure
- `src/users`: Custom user management with role-based access control.
- `src/cooperatives`: Management of cooperatives, members, farms, and records.
- `src/questionnaires`: Dynamic survey and data collection engine.
- `src/analytics`: KPI definition and report generation.
- `src/sync`: Offline data synchronization service.

## Setup Instructions
1. Clone the repository.
2. Configure `.env` based on `.env.example`.
3. Run `docker-compose up --build`.
4. Access the application at `http://localhost:8000`.

## Documentation
Technical design details can be found in `CO3DATA_Technical_Design.md`.

### Guides & References
- **User Guide:** `docs/USER_GUIDE.md` — step‑by‑step workflows for everyday users.
- **Architecture & Design:** `docs/ARCHITECTURE.md` — system architecture, data flow, and multi-tenant strategies.
- **Development Handbook:** `docs/DEVELOPMENT.md` — coding standards, testing, and contribution guidelines.
- **Operational Playbooks:** `docs/DEPLOYMENT.md`, `docs/LAUNCH_READINESS.md`, `docs/INCIDENT_RESPONSE.md`.
- **Training & Support:** `docs/TRAINING_SUPPORT.md` — runbooks and slide templates for onboarding.

### Project Management Artifacts
- **User Stories & Epics:** See `FEATURE_MATRIX_AND_WORKFLOWS.md` for a full breakdown of roles, epics, and sample workflows.
- **UI/UX Improvements:** `UI_UX_IMPROVEMENTS.md` documents design strategies and component patterns added during recent sprints.
- **Testing Guides:** `TESTING_CHECKLIST.md` contains exhaustive QA tasks aligned with user stories.

### Development Strategy
CO3DATA follows Agile principles with the following planning hierarchy:
1. **Epics** represent broad capabilities (eg. "Member Management", "Offline Sync").
2. **User Stories** describe discrete functionality from an end‑user perspective, each tied to acceptance criteria and UI screens.
3. **Tasks** are implementation steps, often corresponding to Django views, templates, or API endpoints.

> Example user story:
> ```
> As a regional officer,
> I want to register a new cooperative,
> so that I can onboard members and begin data collection.
> ```

Design decisions are documented in `implementation/implemtation_update.md` and in‑code comments. All UI components follow a shared design language using Bootstrap 5 and the Falcon theme.

### Contribution & Standards
Refer to `CONTRIBUTING.md` for branch policy, commit message conventions, and review process. All new features must include unit tests and updated documentation. Localization is managed via Django i18n; strings should be wrapped in `{% trans %}` or `gettext_lazy`.

---

## Setup Instructions
1. Clone the repository.
2. Configure `.env` based on `.env.example`.
3. Run `docker-compose up --build`.
4. Access the application at `http://localhost:8000`.
5. Refer to `docs/SETUP.md` for advanced configuration (Postgres, Redis, Celery workers).

## Core Features
- **Inclusive Member Management**: Tracking production and demographic data (gender, youth).
- **Financial Monitoring**: Verifiable financial records for cooperatives and members.
- **Dynamic Questionnaires**: Customizable data collection modules.
- **Real-time Analytics**: KPI tracking and performance dashboards.
- **Offline Synchronization**: Mobile-first architecture for remote field data entry.

## Architecture
- **Backend**: Django (Python 3.12)
- **Database**: PostgreSQL
- **Task Queue**: Celery with Redis
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx & HAProxy

## Project Structure
- `src/users`: Custom user management with role-based access control.
- `src/cooperatives`: Management of cooperatives, members, farms, and records.
- `src/questionnaires`: Dynamic survey and data collection engine.
- `src/analytics`: KPI definition and report generation.
- `src/sync`: Offline data synchronization service.

