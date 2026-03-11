# Contributing to Minibot

We're excited you want to help Minibot grow!

## 🧩 Creating a New Plugin

Minibot uses a simple plugin architecture. Each skill is a Python file in `minibot/plugins/`.

### 1. Create a File
Create `minibot/plugins/your_skill.py`.

### 2. Follow the Template
Use the `@tool` decorator from `..tools`.

```python
from ..tools import tool

# --- SKILL METADATA ---
# Description: What does it do?
# Input: args
# Output: result

@tool(name="your_skill_name", description="Clear description for the LLM. Usage: your_skill_name(arg='val')")
def your_skill_name(arg: str):
    """Docstring explaining the function."""
    try:
        # Your logic here
        return "Success!"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 3. Test It
Just restart Minibot (`python main.py`). The plugin loader will automatically pick up your new file. You should see `🔌 [Plugin] Loaded: your_skill` in the console.

## 💻 Adding Bash Skills

If you prefer shell scripts:
1.  Open `skills.sh`.
2.  Add a new bash function.
3.  Or ask Minibot to do it: "Add a skill called 'check_ram' that runs `free -h`."

## 📝 Pull Requests

1.  Fork the repo.
2.  Create a branch (`git checkout -b feature/amazing-skill`).
3.  Commit your changes.
4.  Push to the branch.
5.  Open a Pull Request.

Happy Hacking! 🤖
