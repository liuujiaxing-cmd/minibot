from typing import Dict, Any, Callable
from functools import wraps
import pkgutil
import importlib
import os
import sys

# --- Tool Registry ---
tools_registry: Dict[str, Dict[str, Any]] = {}

def tool(name: str = None, description: str = None):
    """Decorator to register a function as a tool for the agent."""
    def decorator(func: Callable):
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or "No description provided."
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        tools_registry[tool_name] = {
            "name": tool_name,
            "description": tool_description,
            "func": func
        }
        return wrapper
    return decorator

def get_tools_description() -> str:
    """Format available tools for the LLM prompt."""
    if not tools_registry:
        return "No tools available."
        
    desc = []
    for tool_name, tool_data in tools_registry.items():
        desc.append(f"- {tool_name}: {tool_data['description']}")
    return "\n".join(desc)

def execute_tool(tool_name: str, *args, **kwargs):
    """Execute a registered tool by name."""
    if tool_name in tools_registry:
        try:
            return tools_registry[tool_name]["func"](*args, **kwargs)
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
    return f"Tool '{tool_name}' not found."

def clear_tools_registry() -> None:
    tools_registry.clear()

# --- Plugin Loader ---
def load_plugins(reload: bool = False):
    """Dynamically import all modules in the 'plugins' package."""
    # Assume plugins are in 'minibot/plugins'
    plugins_path = os.path.join(os.path.dirname(__file__), "plugins")
    if not os.path.exists(plugins_path):
        return []

    # Iterate over all files in the plugins directory
    loaded = []
    for _, name, _ in pkgutil.iter_modules([plugins_path]):
        try:
            # Import the module. Since we are inside 'minibot', the package is 'minibot.plugins'
            module_name = f"minibot.plugins.{name}"
            if reload and module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.import_module(module_name)
            print(f"🔌 [Plugin] Loaded: {name}")
            loaded.append(name)
        except Exception as e:
            print(f"⚠️ [Plugin] Failed to load {name}: {e}")
    return loaded

def reload_plugins():
    clear_tools_registry()
    return load_plugins(reload=True)
