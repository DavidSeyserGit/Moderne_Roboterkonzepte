# Moderne_Roboterkonzepte

## Prerequisites

This project requires [uv](https://github.com/astral-sh/uv) to be installed. uv is a fast Python package installer and resolver.

To install uv, run:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create API-Key in Open Router
  **Create API-Key**
   To create an API-Key got to:
   ```bash
   https://openrouter.ai/
   ```
   and select keys, there you can create one.

3. Choose a model, in our case we are choosing:
   ```bash
   x-ai/grok-4.1-fast:free
   ```
   
   To integrate the model in the code change this code segment in main.py and add your favourite model:
   ```bash
   model="x-ai/grok-4.1-fast:free"
   ```
 
4. Set your OpenRouter API key (choose one method):

   **Option A: Using a .env file (recommended)**
   ```bash
   echo "OPENROUTER_API_KEY=your-api-key-here" > .env
   ```

   **Option B: Export as environment variable**
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```

## Usage

Run the main script to make an OpenRouter API call with LangChain and tool calling:

```bash
uv run main.py
```

The script demonstrates how to use LangChain with OpenRouter's API and function calling to control robot navigation using the `move_to_pose` tool. LangChain provides a higher-level abstraction with agents that automatically handle tool calling and conversation flow.