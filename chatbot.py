from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

class Chatbot:
    #Chatbot-Klasse mit LangChain-Speicher und Modellwechsel.
    def __init__(self, api_key: str, model: str):
        self.model_name = model
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        )
        self.messages = []  # Manual message history

    #Wechselt das aktuelle Modell dynamisch.
    def update_model(self, api_key: str, model: str):
        self.model_name = model
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        )

    #Verarbeitet Nutzereingaben mit Memory (async).
    async def get_response(self, user_input: str) -> str:
        self.messages.append(HumanMessage(content=user_input))
        response = await self.llm.ainvoke(self.messages)
        self.messages.append(AIMessage(content=response.content))
        return response.content.strip() if response.content else ""
