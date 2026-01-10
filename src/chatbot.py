from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from tools import available_tools
import chainlit as cl
from pathlib import Path

class Chatbot:
    # Chatbot-Klasse mit Tool-Unterstützung
    def __init__(self, api_key: str, model: str):
        self.model_name = model
        self.api_key = api_key
        self.tools = available_tools
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        ).bind_tools(self.tools) # equal ?????

        # Load system prompt from file (required)
        prompt_path = Path(__file__).parent.parent / "config" / "system_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")
        system_prompt = prompt_path.read_text(encoding="utf-8")

        # Manual message history
        self.messages = [
            SystemMessage(
                content=system_prompt
            )
        ]  

    # Modellwechsel
    def update_model(self, api_key: str, model: str):
        self.model_name = model
        self.api_key = api_key
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        ).bind_tools(self.tools)

    # Verarbeitet Nutzereingaben
    async def get_response(self, user_input: str) -> str:
        self.messages.append(HumanMessage(content=user_input))
        response = await self.llm.ainvoke(self.messages)
        self.messages.append(response)

        # Werkzeugschleife
        while response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # CHAINLIT: Show Thinking-Step
                await cl.Message(
                    content=f"**Modell denkt...**\nEs möchte das Tool **{tool_name}** ausführen."
                ).send()

                # Execute the tool
                if tool_name in self.tools_by_name:
                    tool_result = self.tools_by_name[tool_name].invoke(tool_args)
                else:
                    tool_result = f"Error: Tool '{tool_name}' not found"

                # CHAINLIT: Show tool result
                await cl.Message(
                    content=f"**Tool-Ergebnis von {tool_name}:**\n```\n{tool_result}\n```"
                ).send()

                # Ergebnis dem Modell zurückgeben
                self.messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                )

            # Modellantwort nach Toolausführung abrufen
            response = await self.llm.ainvoke(self.messages)
            self.messages.append(response)

        return response.content.strip() if response.content else ""
