# model_fetcher.py - Fetches available LLM models from OpenRouter API
import requests


class ModelFetcher:
    """Queries OpenRouter API to get available models filtered by capabilities."""

    API_URL = "https://openrouter.ai/api/v1/models"

    def __init__(self):
        # Pricing fields to check when determining if a model is free
        self.price_fields = [
            "prompt", "completion", "request",
            "image", "web_search", "internal_reasoning",
            "input_cache_read", "input_cache_write"
        ]

    def get_models(
        self,
        free: bool = True,
        tools: bool = True,
        vision: bool = False,
        embeddings: bool = False,
        json_mode: bool = False,
        web_search: bool = False,
        reasoning: bool = False,
        cache: bool = False,
    ):
        """
        Fetches models from OpenRouter with optional filters.

        Args:
            free: Only return models where all pricing fields are "0"
            tools: Only models supporting function/tool calling
            vision: Only models supporting image input
            embeddings: Only embedding models
            json_mode: Only models supporting structured JSON output
            web_search: Only models with web search capability
            reasoning: Only models with chain-of-thought reasoning
            cache: Only models supporting prompt caching

        Returns:
            List of model dicts with id, name, description, supported params, pricing
        """
        response = requests.get(self.API_URL)
        if response.status_code != 200:
            raise RuntimeError(f"API request failed: {response.status_code}")

        models = response.json().get("data", [])
        filtered_models = []

        for m in models:
            pricing = m.get("pricing", {})
            supported = m.get("supported_parameters", [])

            # Apply filters - skip model if it doesn't match criteria
            if free and not all(pricing.get(field, "0") == "0" for field in self.price_fields):
                continue
            if tools and "tools" not in supported:
                continue
            if vision and "vision" not in supported:
                continue
            if embeddings and "embeddings" not in supported:
                continue
            if json_mode and "json_mode" not in supported:
                continue
            if web_search and "web_search" not in supported:
                continue
            if reasoning and "reasoning" not in supported:
                continue
            if cache and not any(p in supported for p in ["input_cache_read", "input_cache_write"]):
                continue

            filtered_models.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "description": m.get("description", ""),
                "supported": supported,
                "pricing": pricing
            })

        return filtered_models
