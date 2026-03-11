# Minibot Project Architecture (v2.0)

## 1. Core Architecture: The "Cognitive Agent" Model

Minibot has evolved from a simple chatbot into a sophisticated **Cognitive Agent**. It follows a modular, pipeline-based architecture designed for autonomy, safety, and continuous learning.

### The Brain (Cognitive Pipeline)
The core `Agent` (`minibot/agent.py`) no longer just loops. It executes a structured **9-Step Cognitive Pipeline** for every user message:

1.  **🛡️ Safety Check (Input)**: `SafetyChecker` scans for malicious commands or injection attacks.
2.  **📥 Short-Term Memory**: Stores the immediate conversation context.
3.  **📚 Context Retrieval**: Fetches relevant facts from Long-Term Memory (`minibot_memory.json`).
4.  **🎭 Personality Analysis**: `PersonalityManager` adjusts the bot's tone based on who it's talking to (e.g., using your name).
5.  **📝 Task Planning**: `Planner` decomposes complex requests into a step-by-step plan (if needed).
6.  **⚙️ Prompt Engineering**: Dynamically assembles the System Prompt with tools, context, and plan.
7.  **🔄 ReAct Loop (Reasoning + Acting)**: The classic "Think -> Act -> Observe" loop, now powered by a **Hybrid Tool System**.
8.  **📤 Safety Check (Output)**: Sanitizes the final response.
9.  **🧠 Auto-Memory Extraction**: A background process (`MemoryManager`) analyzes the conversation to learn new facts about the user automatically.

### The Hands (Hybrid Tool System)
Minibot now possesses a unique **Dual-Engine Tool System**:

1.  **Python Tools (`minibot/tools.py`)**: High-level logic and API interactions.
    *   `calculator`: Safe math evaluation.
    *   `install_skill`: Downloads new capabilities from the cloud.
    *   `search_remote_skills`: Finds new skills in the marketplace.
2.  **Bash Skills (`skills.sh`)**: Direct operating system control.
    *   `execute_skill`: Runs bash functions safely.
    *   `add_skill`: Writes new bash functions (Self-Programming).
    *   *Examples*: `open_app`, `set_volume`, `check_battery`, `get_top_news`.

### The Memory (Dual-Layer)
*   **Short-Term**: In-memory `deque` for conversation context.
*   **Long-Term**: JSON-based persistent storage for user facts and preferences.
*   **Auto-Learning**: The `MemoryManager` runs silently to extract facts like "User likes pizza" without explicit instruction.

## 2. Learning Protocol (Autonomy)

Minibot is designed to **never say "I can't"**. When faced with an unknown task, it follows this protocol:

1.  **Search**: Look for a skill in the remote marketplace (`search_remote_skills`).
2.  **Install**: Download the skill code (`install_skill`).
3.  **Execute**: Run the newly acquired skill.
4.  **Create (Fallback)**: If no skill exists, use internal knowledge to write a new Bash script and save it (`add_skill`).

## 3. Safety Mechanism

To allow system control without risk, Minibot implements a **Sandboxed Execution Environment**:

*   **Input Sanitization**: Blocks dangerous commands like `rm -rf`, `mkfs`, etc.
*   **Argument Validation**: Tools only accept safe characters (alphanumeric).
*   **Transactional Writes**: `add_skill` verifies syntax before saving to `skills.sh` to prevent corruption.
*   **White-listing**: Only specific Bash functions can be executed.

## 4. Data Flow

1.  **User**: "Check my battery."
2.  **Agent**:
    *   Checks safety -> OK.
    *   Plans -> "I need to run a battery check command."
    *   **ReAct**:
        *   Thought: "I don't have a native Python tool for battery. Let me check `skills.sh`."
        *   Action: `execute_skill('check_battery')`
        *   Observation: "85%"
    *   **Auto-Memory**: (Background) "User is interested in battery life."
3.  **Response**: "Your battery is at 85%."
