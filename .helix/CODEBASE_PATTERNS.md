# Codebase Patterns & Conventions

<!-- @helix generated — derived from project architecture and SRS -->

These patterns are inferred from the project's architecture document and SRS specifications. Follow them for consistency.

## Backend Route Pattern

- Framework: FastAPI (Python)
- Use `async def` for all route handlers
- Use dependency injection via `Depends()`
- API versioning: `/api/v1/` prefix

## Service Layer Pattern

- Business logic lives in service classes/functions, not in route handlers
- Routes validate input, call service, return response
- API responses use a JSON envelope pattern

## Frontend Component Pattern

- Library: React
- Use functional components with hooks

## Data Layer Pattern

- Database: PostgreSQL
- Schema migrations managed via Alembic

## Testing Pattern

- Place tests adjacent to source or in a `tests/` directory
- Name test files: `test_<module>.py` or `<module>.test.ts`

## Error Handling Pattern

- Follow the error handling matrix from the SRS for status codes
