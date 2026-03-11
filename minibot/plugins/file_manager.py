from ..tools import tool

# --- SKILL METADATA ---
# Description: Manage local files (read/write/find).
# Constraints: Do not read binary files. Max read size 2000 chars.

@tool(name="read_file", description="Read the content of a file. Usage: read_file(path='/tmp/test.txt')")
def read_file(path: str):
    """Read a file from the local filesystem."""
    try:
        with open(path, "r") as f:
            content = f.read()
        return content[:2000] + ("\n... (truncated)" if len(content) > 2000 else "")
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool(name="write_file", description="Write content to a file. Usage: write_file(path='/tmp/test.txt', content='Hello World')")
def write_file(path: str, content: str):
    """Write content to a file."""
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"File written successfully to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool(name="find_file", description="Find files by name pattern. Usage: find_file(pattern='*.py', path='.')")
def find_file(pattern: str, path: str = "."):
    """Find files using glob pattern."""
    import glob
    import os
    try:
        files = glob.glob(os.path.join(path, "**", pattern), recursive=True)
        return "\n".join(files[:20]) or "No files found."
    except Exception as e:
        return f"Error finding files: {str(e)}"
