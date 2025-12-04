# Moderne Roboterkonzepte

A chatbot for robot control using LangChain and OpenRouter.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API key:
```bash
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

## Run the App

```bash
chainlit run main.py -w
```

Open http://localhost:8000 in your browser.

## Adding a New Tool

Edit `tools.py`:

```python
@tool
def my_new_tool(param: str) -> str:
    """Description of what the tool does."""
    # Your code here
    return "result"

# Add to the list
available_tools = [move_to_pose, my_new_tool]
```

Restart the app to use the new tool.
