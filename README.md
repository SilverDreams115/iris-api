# IRIS API

Backend base para el proyecto IRIS construido con FastAPI, SQLAlchemy, Alembic, PostgreSQL y Redis.

## Requisitos

- Docker
- Docker Compose

## Variables de entorno

Crea un archivo `.env` basado en `.env.example`.

## Levantar el proyecto

docker compose up --build

## Ejecutar migraciones

docker compose exec api alembic upgrade head

## Documentación

- Swagger UI: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

## Servicios

- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- pgAdmin: http://localhost:5050
## Backend quality status

The backend currently includes:

- reusable validators for ownership and resource integrity
- centralized error messages and exception helpers
- password hashing with pwdlib and Argon2
- structured logging for startup, auth, signal execution, signal rejection, and trade closing
- automated tests for business flows, permissions, and edge cases

## Continuous Integration

A GitHub Actions workflow is included in:

.github/workflows/ci.yml

This workflow runs automatically on push and pull request for the main working branches and executes the test suite with Python 3.11.

## Technical documentation

A short technical overview is available in:

docs/backend_overview.md
