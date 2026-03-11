from ..tools import tool
from ..memory.long_term import LongTermMemory

# --- SKILL METADATA ---
# Description: Access Long-Term Memory.
# Input: key, value
# Output: Success message or recalled value.

@tool(name="remember", description="Remember important user information or facts for later use. Use this when the user says 'remember this' or provides personal info like name, birthday, etc. Usage: remember(key='user_name', value='John Doe')")
def remember(key: str, value: str):
    # For simplicity, we'll instantiate a fresh LongTermMemory to write.
    ltm = LongTermMemory(file_path="minibot_memory.json")
    ltm.add(key, value)
    return f"I have remembered that {key} is {value}."

@tool(name="recall", description="Recall a specific fact from long-term memory. Use this when you need to answer a question about the user or past events. Usage: recall(key='user_name')")
def recall(key: str):
    ltm = LongTermMemory(file_path="minibot_memory.json")
    val = ltm.get(key)
    if val:
        return f"The value for {key} is: {val}"
    return f"I don't have a memory for {key}."
