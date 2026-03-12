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
