# Minibot: The Cognitive AI Agent

![Minibot Logo](https://img.shields.io/badge/Minibot-v2.0-blueviolet?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.14+-blue?style=for-the-badge) ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

[English](README.md) | [简体中文](README_zh.md)

Minibot is an autonomous, plugin-based AI agent designed for **continuous learning** and **desktop automation**. Unlike traditional chatbots, Minibot can modify its own capabilities, manage long-term memory, and integrate with the open-source agent skills ecosystem (Vercel Skills).

## 🌟 Key Features

*   **🧠 Cognitive Pipeline**: A 9-step reasoning loop (Safety -> Memory -> Plan -> Act -> Observe).
*   **🔌 Micro-Kernel Plugin System**: Capabilities are modular `.py` files. Drop a file, get a skill.
*   **🛠️ Vercel Skills Integration**: Seamlessly install community skills using `find_skills` and `add_skill_from_git` (compatible with `npx skills`).
*   **💻 Bash Autonomy**: Can write its own Bash scripts (`skills.sh`) to control your OS (macOS/Linux).
*   **🎨 Rich TUI**: A beautiful, hacker-style terminal interface with real-time thinking logs.
*   **⏰ Cron Scheduling**: "Remind me to check news every morning at 8."

## 🚀 Quick Start

1.  **Clone & Install**:
    ```bash
    git clone https://github.com/yourusername/minibot.git
    cd minibot
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configure**:
    Create a `.env` file with your API keys:
    ```bash
    OPENAI_API_KEY=sk-...
    # Optional: Telegram Token
    # TELEGRAM_TOKEN=...
    ```

3.  **Run**:
    ```bash
    python main.py
    ```

## 🧩 Plugin System

Minibot's power lies in its `minibot/plugins/` directory.

### Built-in Plugins
*   `web_search`: Real-time internet search (DuckDuckGo).
*   `file_manager`: Read/Write/Find files.
*   `python_exec`: Safe Python code execution.
*   `bash_skills`: Manage `skills.sh` and self-programming.
*   `find_skills`: Discover skills from local and remote registries.

### Installing New Skills
You can ask Minibot to install skills for you:
> "Find a skill for React best practices."
> "Install vercel-labs/agent-skills@react-best-practices."

## 🏗️ Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for a deep dive into the Cognitive Pipeline and Dual-Engine Tool System.

## 📂 File Structure

```
minibot/
├── main.py              # Entry point
├── skills.sh            # Local Bash skills library (self-modifiable)
├── minibot/             # Core package
│   ├── agent.py         # Cognitive loop & reasoning engine
│   ├── tools.py         # Tool registry & plugin loader
│   ├── ui.py            # Rich Terminal UI
│   ├── config.py        # Configuration management
│   ├── connectors/      # Interface adapters (Console, Telegram)
│   ├── memory/          # Long-term (JSON) & Short-term memory
│   ├── modules/         # System modules (Scheduler)
│   └── plugins/         # 🔌 Skill Plugins (Python files)
│       ├── bash_skills.py    # Bash bridge & skill installer
│       ├── find_skills.py    # Skill discovery (Local + Vercel)
│       ├── web_search.py     # Internet access
│       └── ...
└── requirements.txt     # Dependencies
```

## 🤝 Contributing

We love contributions! Whether it's a new Python plugin or a clever Bash script.
Check out [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## 📄 License

MIT © [Your Name]
