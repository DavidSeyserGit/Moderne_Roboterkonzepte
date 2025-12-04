from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from tools import available_tools

class Chatbot:
    #Chatbot-Klasse mit LangChain-Speicher und Modellwechsel.
    def __init__(self, api_key: str, model: str):
        self.model_name = model
        self.api_key = api_key
        self.tools = available_tools
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        ).bind_tools(self.tools)
        self.messages = []  # Manual message history

    #Wechselt das aktuelle Modell dynamisch.
    def update_model(self, api_key: str, model: str):
        self.model_name = model
        self.api_key = api_key
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        ).bind_tools(self.tools)

    #Verarbeitet Nutzereingaben mit Memory (async).
    async def get_response(self, user_input: str) -> str:
        self.messages.append(HumanMessage(content=user_input))
        response = await self.llm.ainvoke(self.messages)
        self.messages.append(response)
        
        # Handle tool calls if present
        while response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Execute the tool
                if tool_name in self.tools_by_name:
                    tool_result = self.tools_by_name[tool_name].invoke(tool_args)
                else:
                    tool_result = f"Error: Tool '{tool_name}' not found"
                
                # Add tool result to messages
                self.messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                )
            
            # Get next response after tool execution
            response = await self.llm.ainvoke(self.messages)
            self.messages.append(response)
        
        return response.content.strip() if response.content else ""
