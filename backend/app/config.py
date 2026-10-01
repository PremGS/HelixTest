"""Application configuration.

Settings are sourced from environment variables (optionally via a local
``.env`` file) using ``pydantic-settings``. This scaffold defines the
configuration surface implied by the SLLIP architecture (see
``.helix/ARCHITECTURE.md``) for Azure OpenAI, Azure Cosmos DB, Azure AI
Search, Azure Blob Storage, and CATS SSO — none of the values are used to
make real network calls yet.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the SLLIP backend.

    All fields have safe local-development defaults so the app can be run
    without any Azure resources provisioned.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # General
    app_name: str = "SLLIP Backend"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment: str = "gpt-4.1"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"

    # Azure Cosmos DB
    azure_cosmos_endpoint: str = ""
    azure_cosmos_key: str = ""
    azure_cosmos_database: str = "sllip"

    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""
    azure_search_index_name: str = "sllip-documents"

    # Azure Blob Storage
    azure_storage_account_url: str = ""
    azure_storage_connection_string: str = ""
    azure_storage_container_name: str = "documents"

    # Azure Document Intelligence
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_api_key: str = ""

    # CATS SSO (OIDC/OAuth2)
    cats_sso_issuer: str = ""
    cats_sso_audience: str = ""
    cats_sso_jwks_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    Using ``lru_cache`` means the environment is only parsed once per
    process, matching common FastAPI dependency-injection patterns.
    """

    return Settings()
