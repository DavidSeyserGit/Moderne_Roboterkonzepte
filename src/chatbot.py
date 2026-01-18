# chatbot.py - LLM chatbot with tool/function calling support
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from tools import available_tools
import chainlit as cl
from pathlib import Path


class Chatbot:
    """
    Chatbot that uses LangChain to interact with LLMs via OpenRouter.
    Supports tool calling - the LLM can request to execute functions (like move_to_pose, search_docs)
    and receive results back to form its final answer.
    """

    def __init__(self, api_key: str, model: str):
        self.model_name = model
        self.api_key = api_key
        self.tools = available_tools

        # Create lookup dict: tool_name -> tool_function for quick access
        self.tools_by_name = {tool.name: tool for tool in self.tools}

        # Initialize LLM with OpenRouter as backend
        # bind_tools() tells the LLM about available tools and their schemas
        # bind_tools() is equivalent to adding a ToolCallAgent wrapper around the LLM or adding tool=[] in LangChain Chains
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        ).bind_tools(self.tools)

        # Load system prompt from config file
        # we store it seperately to keep the code clean and allow easy editing
        prompt_path = Path(__file__).parent.parent / "config" / "system_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")
        system_prompt = prompt_path.read_text(encoding="utf-8")

        # Message history - maintains conversation context (for each chat session)
        # Starts with system prompt that defines the bot's behavior
        self.messages = [
            SystemMessage(content=system_prompt)
        ]

    def update_model(self, api_key: str, model: str):
        """Switches to a different LLM model while keeping conversation history."""
        self.model_name = model
        self.api_key = api_key
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        ).bind_tools(self.tools)

    async def get_response(self, user_input: str) -> str:
        """
        Processes user input and returns the LLM's response.
        Handles the tool-calling loop if the LLM requests tool execution.
        """
        # Add user message to history
        self.messages.append(HumanMessage(content=user_input))

        # Get initial LLM response (may contain tool_calls)
        response = await self.llm.ainvoke(self.messages)
        self.messages.append(response)

        # Tool loop: if LLM wants to call tools, execute them and continue
        # This loop handles multi-step reasoning where LLM may call multiple tools
        while response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Show user that the model is "thinking" and using a tool
                await cl.Message(
                    content=f"**Modell denkt...**\nEs möchte das Tool **{tool_name}** ausführen."
                ).send()

                # Execute the requested tool
                if tool_name in self.tools_by_name:
                    tool_result = self.tools_by_name[tool_name].invoke(tool_args)
                else:
                    tool_result = f"Error: Tool '{tool_name}' not found"

                # Show tool result to user
                await cl.Message(
                    content=f"**Tool-Ergebnis von {tool_name}:**\n```\n{tool_result}\n```"
                ).send()

                # Add tool result to conversation so LLM can use it
                # ToolMessage links result back to the specific tool_call via ID
                self.messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                )

            # Get next LLM response (may request more tools or give final answer)
            response = await self.llm.ainvoke(self.messages)
            self.messages.append(response)

        # Return final text response (after all tools are done)
        return response.content.strip() if response.content else ""
