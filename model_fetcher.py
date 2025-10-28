import requests

class ModelFetcher:
    #Durchsucht alle verfügbaren Modelle nach den gewünschten Funktionen.
    API_URL = "https://openrouter.ai/api/v1/models"

    def __init__(self):
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
        Lädt Modelle von OpenRouter mit flexiblen Filtern.
        Parameter:
            free (bool): Nur kostenlose Modelle anzeigen
            tools (bool): Nur Modelle mit Tool-Unterstützung anzeigen
            vision (bool): Nur Modelle mit Vision-Unterstützung anzeigen
            embeddings (bool): Nur Embedding-Modelle anzeigen
            json_mode (bool): Nur Modelle mit JSON-Unterstützung anzeigen
            web_search (bool): Nur Modelle mit Websuche anzeigen
            reasoning (bool): Nur Modelle mit internem Reasoning anzeigen
            cache (bool): Nur Modelle mit Cache-Unterstützung anzeigen
        """
        response = requests.get(self.API_URL)
        if response.status_code != 200:
            raise RuntimeError(f"API request failed: {response.status_code}")

        models = response.json().get("data", [])
        filtered_models = []

        for m in models:
            pricing = m.get("pricing", {})
            supported = m.get("supported_parameters", [])

            # Preisfilter
            if free and not all(pricing.get(field, "0") == "0" for field in self.price_fields):
                continue

            # Parameterfilter
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
