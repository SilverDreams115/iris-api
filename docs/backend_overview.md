# IRIS API Backend Overview

## Current status
The backend currently includes:
- FastAPI application structure
- JWT authentication
- password hashing with passlib + bcrypt
- CRUD endpoints for core trading resources
- reusable validators and centralized error handling
- automated tests for core flows
- readiness checks for database and Redis
- environment-based CORS configuration

## Main modules

### app/api
HTTP routes and endpoint behavior.

### app/core
Shared configuration and utilities.
- settings.py
- security.py
- logging.py
- exceptions.py
- error_messages.py
- redis_client.py

### app/crud
Database persistence logic.

### app/services
Business rules separated from routes.

### app/schemas
Request and response schemas.

### app/models
SQLAlchemy models for:
- User
- Portfolio
- BrokerAccount
- Strategy
- Trade
- Signal

## Current quality protections
- centralized error messages
- reusable validation helpers
- structured logging
- automated tests
- CI workflow with pytest and coverage

## Recommended next steps
1. add linting and type checks to CI
2. improve deployment notes for staging and production
3. document endpoint permissions in more detail
4. consider cookie-based auth if product scope grows
