from ..tools import tool
import subprocess

# --- SKILL METADATA ---
# Description: Execute Python code safely.
# Input: code (string)
# Output: Execution result or error.

@tool(name="run_python", description="Execute a Python script or code snippet. Usage: run_python(code='print(1+1)')")
def run_python(code: str):
    """Execute Python code safely (in a subprocess)."""
    try:
        # Create a temporary file
        temp_file = "temp_script.py"
        with open(temp_file, "w") as f:
            f.write(code)
            
        result = subprocess.run(
            ["python3", temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout.strip() or result.stderr.strip()
        return output
    except Exception as e:
        return f"Python execution failed: {str(e)}"
