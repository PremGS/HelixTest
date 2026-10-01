# SLLIP Backend

This is the scaffolded Python backend for the **SLLIP** (Azure-native Serverless
LangGraph-based Legal/Policy Intelligence Platform) architecture described in
[`.helix/ARCHITECTURE.md`](../.helix/ARCHITECTURE.md).

It implements the FastAPI Orchestration Service and Document Ingestion Service
described in that document as a **runnable scaffold**: routing, request/response
shapes, and service/agent interfaces are all in place, but the actual calls to
Azure OpenAI, Azure AI Search, Azure Cosmos DB, Azure Blob Storage, and Azure
Document Intelligence are stubbed out with `TODO` comments and, where
appropriate, `NotImplementedError`.

## Project layout

```
backend/
  app/
    main.py           FastAPI app entrypoint, mounts the API routers
    config.py         Settings (env vars) via pydantic-settings
    dependencies.py   Auth dependency stub for CATS SSO JWTs
    models/           Pydantic schemas mirroring the Cosmos DB ER diagram
    api/v1/           Versioned REST API routers (documents, queries, audit, conversations, health)
    services/         Stub wrappers around Azure services (Blob, AI Search, Cosmos DB, OpenAI) and the ingestion/orchestration services
    agents/           LangGraph multi-agent pipeline (planner -> retrieval -> critique)
    core/             Cross-cutting concerns: logging, security/JWT helpers
  tests/              Pytest test suite
```

## Requirements

- Python 3.11+

## Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the app locally

```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs are at
`http://127.0.0.1:8000/docs`.

Health check:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

## Configuration

All settings are read from environment variables (see `app/config.py`), and can
be supplied via a `.env` file in the `backend/` directory. None of the Azure
service calls are made for real in this scaffold, so these values can be left
blank for local development.

Key environment variables:

- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `AZURE_COSMOS_ENDPOINT`, `AZURE_COSMOS_KEY`, `AZURE_COSMOS_DATABASE`
- `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `AZURE_SEARCH_INDEX_NAME`
- `AZURE_STORAGE_ACCOUNT_URL`, `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_STORAGE_CONTAINER_NAME`
- `CATS_SSO_ISSUER`, `CATS_SSO_AUDIENCE`, `CATS_SSO_JWKS_URL`

## Running tests

```bash
cd backend
pytest
```

## Next steps (not implemented in this scaffold)

- Wire real Azure SDK clients into the `services/` modules.
- Implement JWT signature verification against the CATS SSO JWKS endpoint in `core/security.py`. **Important:** until this is done, `get_current_user` deliberately rejects *all* requests when `environment != "local"`, since it currently only decodes tokens without verifying their signature. Do not deploy this scaffold to a non-local environment without completing this step first.
- Replace the stub LangGraph nodes in `agents/` with real LangChain chains/tools.
- Add persistence-backed status tracking for document ingestion and query processing.
