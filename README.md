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

2. Set your OpenRouter API key (choose one method):

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
