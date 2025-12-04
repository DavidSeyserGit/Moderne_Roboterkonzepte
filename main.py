import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from tools import move_to_pose

# Load environment variables
load_dotenv()


class MoveToPoseInput(BaseModel):
    """Input schema for move_to_pose tool"""
    pose_str: str = Field(
        description="A YAML string containing the pose with keys: x (float), y (float), and theta (float in radians). Example: 'x: 1.0\\ny: 2.0\\ntheta: 0.5'"
    )


def main():
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return

    # Initialize ChatOpenAI with OpenRouter
    llm = ChatOpenAI(
        model="x-ai/grok-4-fast:free",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0
    )

    # Create tools with proper schema
    tools = [
        StructuredTool.from_function(
            func=move_to_pose,
            name="move_to_pose",
            description="Sends a navigation goal to the nav2 stack to move the robot to a specific pose in the map frame. The pose includes x, y coordinates and theta (orientation angle in radians).",
            args_schema=MoveToPoseInput,
            return_direct=False
        )
    ]

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful robot navigation assistant. Use the available tools to help move the robot to specified positions."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Get user input from terminal
    user_input = input("Enter your message: ")

    print(f"User: {user_input}\n")

    # Execute the agent
    result = agent_executor.invoke({"input": user_input})

    print(f"\nFinal Result: {result['output']}")


if __name__ == "__main__":
    main()

