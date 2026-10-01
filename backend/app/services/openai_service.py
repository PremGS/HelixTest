"""Stub wrapper around the Azure OpenAI client (chat completions + embeddings).

See the "Azure OpenAI (GPT-4.1)" component in ``.helix/ARCHITECTURE.md``: the
primary LLM for natural language understanding, document analysis,
summarisation, and AI response generation, plus Text Embedding 3 Large for
vectorization.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings


class OpenAIService:
    """Thin wrapper around ``openai.AzureOpenAI`` / ``AsyncAzureOpenAI``."""

    def __init__(self) -> None:
        self._settings = get_settings()
        # TODO: instantiate openai.AsyncAzureOpenAI with
        # azure_endpoint=settings.azure_openai_endpoint,
        # api_key=settings.azure_openai_api_key (or Managed Identity/AAD
        # token provider), and api_version=settings.azure_openai_api_version.
        self._client = None

    async def create_embedding(self, text: str) -> list[float]:
        """Generate an embedding vector for ``text`` using Text Embedding 3 Large.

        TODO: call ``self._client.embeddings.create`` with
        ``model=settings.azure_openai_embedding_deployment``.
        """

        raise NotImplementedError("OpenAIService.create_embedding is not implemented")

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a chat completion using GPT-4.1.

        TODO: call ``self._client.chat.completions.create`` with
        ``model=settings.azure_openai_deployment`` and return the generated
        text plus token usage.
        """

        raise NotImplementedError("OpenAIService.chat_completion is not implemented")
