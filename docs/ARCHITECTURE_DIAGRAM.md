# Minibot Architecture Diagram

![Minibot Architecture Visualization](https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=Futuristic%20software%20architecture%20diagram%20of%20Minibot%20AI%20Agent.%20Central%20glowing%20core%20processor.%20Modules%20for%20Memory%2C%20Tools%2C%20and%20LLM%20connected%20via%20data%20streams.%20Dark%20blue%20blueprint%20style%2C%20neon%20cyan%20and%20purple%20accents%2C%20isometric%20view%2C%20high%20detail%2C%204k%2C%20tech%20schematic&image_size=landscape_16_9)

```mermaid
graph TD
    subgraph "External World"
        User([User])
        Telegram[Telegram API]
        Ollama[Ollama / DeepSeek API]
        Marketplace[Skill Marketplace]
    end

    subgraph "Minibot Core System"
        
        subgraph "Senses (Connectors)"
            ConsoleConn[Console Connector]
            TeleConn[Telegram Connector]
        end

        subgraph "Brain (Cognitive Pipeline)"
            Safety[Safety Checker]
            Planner[Task Planner]
            Personality[Personality Manager]
            MemManager[Auto-Memory Extractor]
            AgentLogic[ReAct Agent Loop]
        end

        subgraph "Memory System"
            STM[Short-Term Memory\n(In-Memory Deque)]
            LTM[Long-Term Memory\n(JSON File)]
        end

        subgraph "Capabilities (Tools)"
            ToolReg[Python Tool Registry]
            SkillsSH[Bash Skill Library (skills.sh)]
            
            subgraph "Python Tools"
                CalcTool[Calculator]
                TimeTool[Get Time]
                MemTool[Remember/Recall]
                InstallTool[Install Skill]
            end
            
            subgraph "Bash Skills"
                SysInfo[System Info]
                RemoteSkill[Remote Skills...]
            end
        end

        subgraph "Knowledge (LLM Layer)"
            LLMClient[LLM Client Wrapper]
        end

    end

    %% Data Flow
    User <--> ConsoleConn
    User <--> Telegram <--> TeleConn

    ConsoleConn -->|Raw Input| Safety
    TeleConn -->|Raw Input| Safety

    Safety -->|Safe Input| STM
    STM -->|Context| Planner
    LTM -->|Context| Planner
    
    Planner -->|Decomposed Plan| Personality
    Personality -->|Style Instructions| AgentLogic

    AgentLogic -->|Prompt| LLMClient
    LLMClient <-->|API Call| Ollama
    LLMClient -->|Thought/Action| AgentLogic

    %% Memory Loop
    AgentLogic -.->|Background Extraction| MemManager
    MemManager -->|Update| LTM

    %% Tool Execution
    AgentLogic -- "Call Tool" --> ToolReg
    ToolReg -->|Run| CalcTool
    ToolReg -->|Run| InstallTool
    InstallTool <-->|Download| Marketplace
    
    ToolReg -- "Execute Skill" --> SkillsSH
    SkillsSH -->|Run Bash Function| SysInfo

    %% Output
    AgentLogic -->|Final Response| Safety
    Safety -->|Sanitized Output| ConsoleConn
```

## Flow Description (Updated)

1.  **Input & Safety**: User input is first checked by `SafetyChecker` for malicious commands.
2.  **Context & Planning**: 
    *   `ShortTermMemory` and `LongTermMemory` provide context.
    *   `Planner` decomposes complex requests into steps.
    *   `PersonalityManager` adjusts the tone based on user profile.
3.  **Reasoning (ReAct)**: The `Agent` sends the full prompt (Context + Plan + Style) to the LLM.
4.  **Action (Hybrid Tools)**:
    *   **Python Tools**: Standard logic like `calculator` or `install_skill` (which downloads from the Marketplace).
    *   **Bash Skills**: `execute_skill` calls functions in `skills.sh`, allowing direct system interaction.
5.  **Memory Evolution**:
    *   **Auto-Extraction**: A background process (`MemoryManager`) analyzes the conversation and updates `LongTermMemory` silently.
    *   **Skill Learning**: `install_skill` adds new capabilities to `skills.sh`.
6.  **Output**: The final response is sanitized again before being shown to the user.
