# Comparison: Minibot vs. Nanobot

This document provides a detailed architectural comparison between Minibot (this project) and Nanobot (the inspiration).

## 1. Architecture Overview

### Minibot: The Modular "Brain-in-a-Box"
Minibot is designed as a **cognitive pipeline**. It treats the agent as a series of processing steps (Safety -> Memory -> Planning -> Action).
*   **Core Philosophy**: "Explicit over Implicit". Every step of the thought process is visible and modular.
*   **Key Components**:
    *   `Agent`: The central orchestrator.
    *   `MemoryManager`: Automatic background fact extraction.
    *   `Planner`: Explicit task decomposition for complex queries.
    *   `Skills.sh`: A unique hybrid approach mixing Python logic with raw Bash scripts.
*   **Data Flow**: Linear pipeline with a feedback loop (ReAct).

### Nanobot: The Lightweight Script
Nanobot is typically a single-file or few-file script focused on **simplicity and speed**.
*   **Core Philosophy**: "Just make it work". It often hardcodes the loop and relies heavily on the LLM's native capabilities without much structural scaffolding.
*   **Key Components**: A single loop that calls the LLM and executes Python functions.
*   **Data Flow**: Direct User -> LLM -> Function -> LLM -> User.

## 2. Detailed Comparison

| Feature | Minibot | Nanobot |
| :--- | :--- | :--- |
| **Cognitive Architecture** | **Advanced**: Includes Safety, Planning, Personality, and Auto-Memory modules. | **Basic**: Primarily a prompt + tool loop. |
| **Tool System** | **Hybrid**: Python (`@tool`) + Bash (`skills.sh`) + Remote Market. | **Python Only**: Usually just local functions. |
| **Memory** | **Dual Layer**: Short-term (Deque) + Long-term (JSON) + Auto-Extraction. | **Single Layer**: Usually just conversation history or simple file append. |
| **Extensibility** | **High**: Module-based. You can plug in a new "Planner" or "Safety" module easily. | **Medium**: You have to modify the main loop code directly. |
| **Safety** | **Built-in**: `SafetyChecker` sanitizes inputs/outputs. | **Minimal**: Relies on the LLM to behave. |
| **Local LLM Support** | **First-Class**: Optimized for Ollama/DeepSeek with specific prompts. | **Basic**: Often optimized for OpenAI GPT-4. |

## 3. Pros & Cons

### Minibot

**✅ Pros:**
*   **Smarter**: The "Planner" and "Memory" modules make it behave more like a real assistant than a chatbot.
*   **Safer**: Input/output sanitization prevents basic injection attacks.
*   **More Powerful Tools**: The `skills.sh` integration allows it to use any Linux command safely.
*   **Self-Evolving**: Can download new skills from a (mock) marketplace and learn new facts automatically.

**❌ Cons:**
*   **Slightly More Complex**: Requires understanding the "Pipeline" concept (Safety -> Plan -> Act).
*   **Latency**: The multi-step pipeline (e.g., auto-memory extraction) adds a small delay compared to a raw API call (though we use async to mitigate this).

### Nanobot

**✅ Pros:**
*   **Dead Simple**: Often just one file. easier to copy-paste.
*   **Fast**: Minimal overhead between the user and the LLM.

**❌ Cons:**
*   **"Goldfish Memory"**: Often forgets context or facts once the session ends.
*   **Hard to Scale**: Adding complex logic (like "don't say X words" or "plan before doing") turns the code into spaghetti.
*   **Fragile**: If the LLM hallucinates a tool call, the script often crashes. Minibot has robust error handling and fallback parsing.

## Conclusion

*   **Choose Nanobot** if you need a 50-line script to test an API key or do a quick one-off task.
*   **Choose Minibot** if you want to build a **personal assistant** that remembers you, grows with you, and can handle complex tasks safely on your local machine.

