# IRIS API Backend Overview

## Current status
The backend is currently in a stable base state with:
- FastAPI application structure
- authentication with JWT
- password hashing with pwdlib + Argon2
- CRUD endpoints for core trading resources
- cross-resource integrity validation
- reusable validators and centralized error messages
- automated test coverage for core business flows, permissions, and edge cases

## Main modules

### app/api
Contains route definitions and HTTP layer behavior.

- auth.py: register, login, current user, change password
- user.py: user management endpoints
- portfolio.py: portfolio CRUD
- broker_account.py: broker account CRUD
- strategy.py: strategy CRUD with resource integrity checks
- trade.py: trade CRUD and trade close flow
- signal.py: signal CRUD, execute flow, reject flow

### app/core
Contains shared application-level configuration and utilities.

- settings.py: environment-based configuration
- security.py: JWT and password hashing helpers
- logging.py: centralized logging setup
- exceptions.py: reusable HTTP exception helpers
- error_messages.py: centralized error message constants

### app/crud
Contains database persistence logic.

### app/services
Contains business rules that should not live in routes.

- validators.py: reusable existence, ownership, and integrity checks
- execution.py: signal execution and rejection logic
- trade_closer.py: dedicated trade closing logic

### app/schemas
Contains request and response validation schemas plus enums.

### app/models
Contains SQLAlchemy models for:
- User
- Portfolio
- BrokerAccount
- Strategy
- Trade
- Signal

## Key business rules already enforced

### Ownership and permissions
- non-admin users can only access their own resources
- admin users can access all resources where allowed by endpoint design

### Strategy integrity
- a strategy cannot reference a portfolio and broker account from different owners

### Trade integrity
- a trade cannot reference a strategy and broker account from different owners

### Signal integrity
- a signal cannot reference a trade that belongs to a different strategy
- executed and rejected signal flows are validated by service rules

### Execution constraints
- signals can only be executed when status is pending or triggered
- signals cannot execute if the strategy is inactive
- signals cannot execute if the broker account is not active
- buy and sell price relationships are validated before execution

## Current quality protections
- centralized error messages
- reusable validation helpers
- structured logging for key actions
- automated tests for:
  - metrics
  - signal execution
  - resource integrity
  - permissions and edge cases

## Recommended next steps
1. add linting and formatting checks
2. add coverage reporting
3. add refresh token flow if product scope requires longer sessions
4. document endpoint permissions in more detail
5. add production-grade logging configuration per environment
