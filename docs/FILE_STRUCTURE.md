# Minibot File Structure Documentation

This document explains the purpose and content of each file in the Minibot project.

## Root Directory

-   `main.py`: **Entry Point**.
    -   This is the file you run to start the bot (`python main.py`).
    -   It initializes the `Agent`, sets up the necessary `Connectors` (like Telegram, Console), and starts the main event loop (`asyncio.run(main())`).
-   `requirements.txt`: **Dependencies**.
    -   Lists all external Python libraries required (e.g., `openai`, `python-telegram-bot`).
-   `.env`: **Secrets**.
    -   Stores sensitive configuration like API keys (`OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`). **This file should never be committed to Git.**
-   `.env.example`: **Config Template**.
    -   A template version of `.env` for other developers to copy and fill in.
-   `README.md`: **Project Overview**.
    -   High-level documentation for users.

## Minibot Package (`minibot/`)

This directory contains the core logic of the bot.

-   `minibot/__init__.py`: **Package Init**.
    -   Makes the directory a Python package. Can expose key classes for easier imports.
-   `minibot/config.py`: **Configuration Manager**.
    -   `class Config`: Loads environment variables, validates them (e.g., checks if API key exists), and provides typed access to settings throughout the app.
-   `minibot/llm.py`: **LLM Interface**.
    -   `class LLMClient`: Wraps the OpenAI/Anthropic/Ollama API calls.
    -   Handles the complexity of communicating with different AI providers so the rest of the code doesn't have to worry about it.
-   `minibot/tools.py`: **Tool Registry**.
    -   `@tool`: A decorator to register functions as tools.
    -   `tools_registry`: A dictionary storing all available tools and their metadata.
    -   `execute_tool()`: Safe wrapper to run a tool by name.
    -   `get_tools_description()`: Generates the prompt text that tells the AI what tools are available.
-   `minibot/agent.py`: **The Brain**.
    -   `class Agent`: Implements the ReAct loop.
    -   `process_message()`: The main function called by connectors. It takes user input, manages conversation history, calls the LLM, parses the LLM's decision to use tools, executes them, and returns the final answer.

## Connectors Package (`minibot/connectors/`)

-   `minibot/connectors/base.py`: **Base Connector**.
    -   `class Connector(ABC)`: Defines the standard interface that all connectors must follow (specifically the `run()` method).
-   `minibot/connectors/console.py`: **Console Interface**.
    -   `class ConsoleConnector`: Allows you to chat with the bot directly in your terminal. Useful for testing and debugging without needing a real chat app.
-   `minibot/connectors/telegram.py`: **Telegram Interface**.
    -   `class TelegramConnector`: Connects to the Telegram Bot API. Receives messages from Telegram users and sends replies back.

## Docs Directory (`docs/`)

-   `docs/ARCHITECTURE.md`: High-level architecture explanation.
-   `docs/FILE_STRUCTURE.md`: This file.
-   `docs/COMPARISON.md`: Comparison with other bots.
