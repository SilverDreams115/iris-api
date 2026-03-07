# IRIS API

Backend base para IRIS construido con FastAPI, SQLAlchemy, Alembic, PostgreSQL y Redis.

## Stack
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Redis
- JWT auth
- pwdlib + Argon2
- compatibilidad con bcrypt para migración de hashes legados

## Requisitos
- Docker
- Docker Compose

## Variables de entorno
Crea un archivo `.env` basado en `.env.example`.

Variables principales:
- `APP_NAME`
- `ENVIRONMENT`
- `DEBUG`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `CORS_ORIGINS`

Ejemplo de `CORS_ORIGINS`:
["http://localhost:3000","http://127.0.0.1:3000"]

## Levantar el proyecto
docker compose up --build

## Ejecutar migraciones
docker compose exec api alembic upgrade head

## Documentación
- Swagger UI: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health
- Readiness: http://localhost:8000/ready

## Servicios
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- pgAdmin: http://localhost:5050

## Estado actual
- validadores reutilizables para ownership e integridad
- helpers centralizados de errores
- hashing con pwdlib + Argon2
- compatibilidad con bcrypt para hashes antiguos
- rehash automático de contraseñas antiguas al iniciar sesión
- logging estructurado
- tests automatizados
- workflow de GitHub Actions con tests y coverage
