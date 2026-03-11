from ..tools import tool

# --- SKILL METADATA ---
# Description: Mathematical operations.
# Input: expression
# Output: Result (float/int)

@tool(name="calculator", description="Evaluate a mathematical expression. Supported functions: abs, round, min, max. Usage: calculator(expression='2024 - 1999')")
def calculator(expression: str):
    try:
        # Warning: eval is dangerous in production, but okay for a local personal bot prototype
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
        # Sanitize input: only allow digits, operators, and spaces
        import re
        if not re.match(r'^[\d\+\-\*\/\(\)\.\s]+$', expression):
             return "Error: Only simple arithmetic is allowed."
        return str(eval(expression, {"__builtins__": None}, allowed_names))
    except Exception as e:
        return f"Calculation error: {str(e)}"

@tool(name="get_current_time", description="Get the current date and time. Use this when you need to know 'today', 'now', or calculate age based on the current year. Usage: get_current_time()")
def get_current_time():
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
