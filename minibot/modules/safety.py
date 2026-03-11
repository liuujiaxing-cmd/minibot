import re

class SafetyChecker:
    """Checks input/output for safety violations."""
    
    def __init__(self):
        # Words/patterns that are dangerous if executed as shell commands
        self.banned_words = ["rm -rf", "drop database", "shutdown", "> /dev/null", "mkfs", "dd if="]
        # Only allow alphanumeric, spaces, and simple punctuation in tool args
        self.safe_args_pattern = re.compile(r'^[a-zA-Z0-9\s\.\-_/]+$')
    
    def check_input(self, text: str) -> bool:
        """Return True if safe, False if unsafe."""
        for word in self.banned_words:
            if word in text.lower():
                return False
        return True

    def check_tool_args(self, args: str) -> bool:
        """Strictly validate tool arguments to prevent command injection."""
        # Allow empty args
        if not args:
            return True
        # Check against regex
        return bool(self.safe_args_pattern.match(args))

    def sanitize_output(self, text: str) -> str:
        """Sanitize output if needed."""
        return text
