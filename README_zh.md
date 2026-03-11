# Minibot: 认知型 AI 智能体

![Minibot Logo](https://img.shields.io/badge/Minibot-v2.0-blueviolet?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.14+-blue?style=for-the-badge) ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

[English](README.md) | [简体中文](README_zh.md)

Minibot 是一个基于插件的自主 AI 智能体，专为**持续学习**和**桌面自动化**而设计。与传统聊天机器人不同，Minibot 能够修改自身能力、管理长期记忆，并无缝集成开源的智能体技能生态系统 (Vercel Skills)。

## 🌟 核心特性

*   **🧠 认知流水线**: 拥有严密的 9 步推理循环 (安全检查 -> 记忆检索 -> 规划 -> 行动 -> 观察)。
*   **🔌 微内核插件系统**: 能力即文件。只需将 `.py` 文件放入插件目录，即可获得新技能。
*   **🛠️ Vercel Skills 集成**: 使用 `find_skills` 和 `add_skill_from_git` 轻松安装社区技能（兼容 `npx skills`）。
*   **💻 Bash 自主性**: 能够编写并执行 Bash 脚本 (`skills.sh`) 来操控您的操作系统 (macOS/Linux)。
*   **🎨 极客风终端 UI**: 拥有精美的命令行界面，实时展示思考过程和日志。
*   **⏰ Cron 定时任务**: “每天早上 8 点提醒我看新闻。”

## 🚀 快速开始

1.  **克隆与安装**:
    ```bash
    git clone https://github.com/yourusername/minibot.git
    cd minibot
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **配置**:
    创建一个 `.env` 文件并填入 API Key：
    ```bash
    OPENAI_API_KEY=sk-...
    # 可选: Telegram Token
    # TELEGRAM_TOKEN=...
    ```

3.  **运行**:
    ```bash
    python main.py
    ```

## 🧩 插件系统

Minibot 的核心力量源自 `minibot/plugins/` 目录。

### 内置插件
*   `web_search`: 实时联网搜索 (DuckDuckGo)。
*   `file_manager`: 文件读/写/查找。
*   `python_exec`: 安全的 Python 代码执行器。
*   `bash_skills`: 管理 `skills.sh` 和自我编程能力。
*   `find_skills`: 从本地和远程仓库发现技能。

### 安装新技能
您可以直接命令 Minibot 安装技能：
> “帮我找一个关于 React 最佳实践的技能。”
> “安装 vercel-labs/agent-skills@react-best-practices。”

## 🏗️ 架构设计

请参阅 [ARCHITECTURE.md](docs/ARCHITECTURE.md) 深入了解其认知流水线和双引擎工具系统。

## 📂 文件结构

```
minibot/
├── main.py              # 程序入口
├── skills.sh            # 本地 Bash 技能库（可自我修改）
├── minibot/             # 核心包
│   ├── agent.py         # 认知循环与推理引擎
│   ├── tools.py         # 工具注册表与插件加载器
│   ├── ui.py            # 极客风终端 UI
│   ├── config.py        # 配置管理
│   ├── connectors/      # 接口适配器 (Console, Telegram)
│   ├── memory/          # 长期记忆 (JSON) & 短期记忆
│   ├── modules/         # 系统模块 (调度器)
│   └── plugins/         # 🔌 技能插件 (Python 文件)
│       ├── bash_skills.py    # Bash 桥接与技能安装器
│       ├── find_skills.py    # 技能发现 (本地 + Vercel)
│       ├── web_search.py     # 联网搜索
│       └── ...
└── requirements.txt     # 依赖列表
```

## 🤝 参与贡献

我们欢迎任何形式的贡献！无论是新的 Python 插件还是巧妙的 Bash 脚本。
请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何开始。

## 📄 许可证

MIT © [Your Name]
