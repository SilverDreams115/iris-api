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