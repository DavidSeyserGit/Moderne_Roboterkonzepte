# main.py - Chainlit web UI entry point
import os
from dotenv import load_dotenv
import chainlit as cl
from chainlit.input_widget import Select
from model_fetcher import ModelFetcher
from chatbot import Chatbot
from rag import index_all_pdfs

load_dotenv()  # Load .env file for local development

# Load API key from Docker secret (preferred) or environment variable
secret_path = "/run/secrets/openrouter_api_key"
if os.path.exists(secret_path):
    with open(secret_path, 'r') as f:
        api_key = f.read().strip()
else:
    api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError(
        "OPENROUTER_API_KEY nicht gefunden!\n"
        "Option 1 (Docker secret): Erstelle .env.secret mit: OPENROUTER_API_KEY=your_key\n"
        "Option 2 (env var): Setze OPENROUTER_API_KEY als Umgebungsvariable"
    )

fetcher = ModelFetcher()


@cl.on_chat_start
async def on_chat_start():
    """Called when user opens the chat - sets up model selection and initializes chatbot."""
    index_all_pdfs()  # Ensure PDFs are indexed

    # Fetch all models with tool support from OpenRouter
    all_models = fetcher.get_models(free=False, tools=True)

    if not all_models:
        await cl.Message(content="Keine Modelle mit Tool-Unterstützung gefunden.").send()
        return

    # Separate models into free and paid for display
    free_models = []
    paid_models = []

    for m in all_models:
        pricing = m.get("pricing", {})
        is_free = all(str(pricing.get(field, "0")) == "0" for field in fetcher.price_fields)
        if is_free:
            free_models.append(m)
        else:
            paid_models.append(m)

    # Build display options with [Free]/[Paid] labels
    display_options = []
    id_map = {}  # Maps display string -> actual model ID

    for m in free_models:
        display_str = f"{m['id']} [Free]"
        display_options.append(display_str)
        id_map[display_str] = m['id']

    for m in paid_models:
        display_str = f"{m['id']} [Paid]"
        display_options.append(display_str)
        id_map[display_str] = m['id']

    if not display_options:
        await cl.Message(content="Keine Modelle verfügbar.").send()
        return

    # Store in session for later use
    cl.user_session.set("id_map", id_map)
    cl.user_session.set("api_key", api_key)

    # Show model selector dropdown
    settings = await cl.ChatSettings([
        Select(
            id="ModelDisplay",
            label="Wähle ein OpenRouter-Modell",
            values=display_options,
            initial_index=0,
        )
    ]).send()

    # Get selected model and create chatbot
    chosen_display = settings["ModelDisplay"]
    chosen_model = id_map.get(chosen_display)

    if not chosen_model and display_options:
        chosen_model = id_map[display_options[0]]

    chatbot = Chatbot(api_key, chosen_model)

    cl.user_session.set("chatbot", chatbot)
    cl.user_session.set("model", chosen_model)

    await cl.Message(
        content=f"Modell gesetzt auf **{chosen_model}**.\n\nWillkommen! Stelle mir deine erste Frage!"
    ).send()


@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Called when user changes model in the UI dropdown."""
    new_model_display = settings.get("ModelDisplay")
    old_model = cl.user_session.get("model")

    chatbot: Chatbot = cl.user_session.get("chatbot")
    api_key = cl.user_session.get("api_key")
    id_map = cl.user_session.get("id_map")

    new_model = id_map.get(new_model_display) if id_map else None

    if new_model and new_model != old_model:
        chatbot.update_model(api_key, new_model)
        cl.user_session.set("model", new_model)

        is_free = "[Free]" in new_model_display
        price_info = "Kostenlos" if is_free else "Kostenpflichtig"

        await cl.Message(
            content=f"Modell erfolgreich gewechselt!\n\nNeues Modell: **{new_model}**\nPreis: {price_info}"
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handles incoming user messages - passes to chatbot and returns response."""
    chatbot: Chatbot = cl.user_session.get("chatbot")
    if not chatbot:
        await cl.Message(content="Kein Modell aktiv. Bitte starte den Chat neu.").send()
        return

    # get_response is async - doesn't block while waiting for LLM
    answer = await chatbot.get_response(message.content)

    await cl.Message(content=answer).send()
