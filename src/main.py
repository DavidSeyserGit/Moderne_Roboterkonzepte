# main.py
import os
from dotenv import load_dotenv
import chainlit as cl
from chainlit.input_widget import Select
from model_fetcher import ModelFetcher
from chatbot import Chatbot

from rag import index_all_pdfs

# Load environment variables from .env file (fallback for local development)
load_dotenv()

# ============================================================
# Initialisierung
# ============================================================
# Try to read from Docker secret first (more secure), then fall back to env var
secret_path = "/run/secrets/openrouter_api_key"
if os.path.exists(secret_path):
    with open(secret_path, 'r') as f:
        api_key = f.read().strip()
else:
    # Fallback to environment variable (for local development or if secret not used)
    api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError(
        "OPENROUTER_API_KEY nicht gefunden!\n"
        "Option 1 (Docker secret): Erstelle .env.secret mit: OPENROUTER_API_KEY=your_key\n"
        "Option 2 (env var): Setze OPENROUTER_API_KEY als Umgebungsvariable"
    )
fetcher = ModelFetcher()

# ============================================================
# Chat Start
# ============================================================
@cl.on_chat_start
async def on_chat_start():
    index_all_pdfs()
    """Wird ausgeführt, wenn der Benutzer den Chat startet."""
    # Fetch ALL models with tools (regardless of price)
    all_models = fetcher.get_models(free=False, tools=True)

    if not all_models:
        await cl.Message(
            content="Keine Modelle mit Tool-Unterstützung gefunden."
        ).send()
        return

    # Separate into free and paid based on pricing
    free_models = []
    paid_models = []

    for m in all_models:
        pricing = m.get("pricing", {})
        # Check if all price fields are "0" or 0
        is_free = all(
            str(pricing.get(field, "0")) == "0"
            for field in fetcher.price_fields
        )

        if is_free:
            free_models.append(m)
        else:
            paid_models.append(m)

    # Create display options for ALL models (show both free and paid)
    display_options = []
    id_map = {}

    # Add free models first
    for m in free_models:
        display_str = f"{m['id']} [Free]"
        display_options.append(display_str)
        id_map[display_str] = m['id']

    # Add paid models
    for m in paid_models:
        display_str = f"{m['id']} [Paid]"
        display_options.append(display_str)
        id_map[display_str] = m['id']

    if not display_options:
        await cl.Message(
            content="Keine Modelle verfügbar."
        ).send()
        return

    # Store in session
    cl.user_session.set("id_map", id_map)
    cl.user_session.set("api_key", api_key)

    # Benutzer soll Modell wählen
    settings = await cl.ChatSettings(
        [
            Select(
                id="ModelDisplay",
                label="Wähle ein OpenRouter-Modell",
                values=display_options,
                initial_index=0,
            )
        ]
    ).send()

    # Extract actual model ID from display string
    chosen_display = settings["ModelDisplay"]
    chosen_model = id_map.get(chosen_display)

    if not chosen_model and display_options:
        # Fallback to first model if not found
        chosen_model = id_map[display_options[0]]

    chatbot = Chatbot(api_key, chosen_model)

    # Session speichern
    cl.user_session.set("chatbot", chatbot)
    cl.user_session.set("model", chosen_model)

    await cl.Message(
        content=f"Modell gesetzt auf **{chosen_model}**.\n\nWillkommen! Stelle mir deine erste Frage!"
    ).send()


# ============================================================
# Modell-Wechsel
# ============================================================
@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Reagiert, wenn der Nutzer das Modell im UI ändert."""
    new_model_display = settings.get("ModelDisplay")
    old_model = cl.user_session.get("model")

    chatbot: Chatbot = cl.user_session.get("chatbot")
    api_key = cl.user_session.get("api_key")
    id_map = cl.user_session.get("id_map")

    # Extract actual model ID from display string
    new_model = id_map.get(new_model_display) if id_map else None

    # Handle model change
    if new_model and new_model != old_model:
        chatbot.update_model(api_key, new_model)
        cl.user_session.set("model", new_model)

        # Determine if new model is free or paid
        is_free = "[Free]" in new_model_display
        price_info = "Kostenlos" if is_free else "Kostenpflichtig"

        await cl.Message(
            content=f"Modell erfolgreich gewechselt!\n\nNeues Modell: **{new_model}**\nPreis: {price_info}"
        ).send()


# ============================================================
# Nachrichtenverarbeitung
# ============================================================
@cl.on_message
async def on_message(message: cl.Message):
    """Behandelt eingehende Nachrichten."""
    chatbot: Chatbot = cl.user_session.get("chatbot")
    if not chatbot:
        await cl.Message(content="Kein Modell aktiv. Bitte starte den Chat neu.").send()
        return

    answer = await chatbot.get_response(message.content)
    #await -> nicht blockend wartet bis roboter dort ist 

    # Send the response
    await cl.Message(content=answer).send()
