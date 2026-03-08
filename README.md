# MTS Fleet API

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 ORM
- Alembic migrations
- PostgreSQL
- JWT bearer auth
- S3 presigned URL generation
- Docker Compose startup that waits for Postgres, runs migrations, then starts the API

## Project setup

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000` and the interactive docs at `http://localhost:8000/docs`.

3. Run migrations:

```bash
alembic upgrade head
```

4. Start the API:

```bash
uvicorn main:app --reload
```

## Alembic commands

Create a new revision:

```bash
alembic revision --autogenerate -m "describe change"
```

Apply all migrations:

```bash
alembic upgrade head
```

Roll back one revision:

```bash
alembic downgrade -1
```

Check current revision:

```bash
alembic current
```
