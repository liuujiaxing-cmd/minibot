from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status
from rich.prompt import Prompt
from rich.table import Table
from rich import box
from rich.theme import Theme
from datetime import datetime

# Define a high-contrast theme for dark terminals
minibot_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
    "default": "bright_white",
    "markdown.paragraph": "bright_white",
    "markdown.text": "bright_white",
    "markdown.item": "bright_white",
    "markdown.list": "bright_white",
    "markdown.header": "bold bright_cyan",
    "markdown.code": "bold yellow",
    "markdown.code_block": "cyan",
    "log.message": "bright_white",
    "log.time": "dim cyan",
})

console = Console(theme=minibot_theme, style="bright_white")

class MinibotUI:
    """Handles rich terminal UI rendering."""
    
    def __init__(self):
        self.console = console
        self.status = None

    def display_welcome(self):
        """Show startup banner."""
        self.console.clear()
        title = """
███╗   ███╗██╗███╗   ██╗██╗██████╗  ██████╗ ████████╗
████╗ ████║██║████╗  ██║██║██╔══██╗██╔═══██╗╚══██╔══╝
██╔████╔██║██║██╔██╗ ██║██║██████╔╝██║   ██║   ██║   
██║╚██╔╝██║██║██║╚██╗██║██║██╔══██╗██║   ██║   ██║   
██║ ╚═╝ ██║██║██║ ╚████║██║██████╔╝╚██████╔╝   ██║   
╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝╚═════╝  ╚═════╝    ╚═╝   
        """
        self.console.print(Panel(
            f"[bold bright_cyan]{title}[/bold bright_cyan]\n[grey70]v2.0 - Cognitive Agent with Plugin System[/grey70]",
            box=box.DOUBLE,
            border_style="bright_cyan"
        ))

    def get_user_input(self) -> str:
        """Get input with styling."""
        return Prompt.ask("\n[bold bright_green]👤 You[/bold bright_green]")

    def display_assistant_response(self, text: str):
        """Render AI response as Markdown."""
        self.console.print("\n[bold bright_magenta]Minibot[/bold bright_magenta]")
        self.console.print(Markdown(text))

    def start_thinking(self, message="Thinking..."):
        """Start a spinner."""
        if self.status:
            self.status.stop()
        self.status = self.console.status(f"[bold yellow]{message}[/bold yellow]", spinner="dots")
        self.status.start()

    def stop_thinking(self):
        """Stop the spinner."""
        if self.status:
            self.status.stop()
            self.status = None

    def log_event(self, event_type: str, message: str, details: str = ""):
        """Log internal events (Safety, Tool, Plan)."""
        # Stop spinner briefly to print log
        if self.status:
            self.status.stop()
        
        icon = "🔹"
        color = "bright_white"
        
        if event_type == "TOOL":
            icon = "🛠️"
            color = "bright_blue"
        elif event_type == "SAFETY":
            icon = "🛡️"
            color = "bright_green"
        elif event_type == "PLAN":
            icon = "📝"
            color = "bright_magenta"
        elif event_type == "MEMORY":
            icon = "🧠"
            color = "bright_cyan"
        elif event_type == "ERROR":
            icon = "❌"
            color = "bright_red"
        elif event_type == "SYSTEM":
            icon = "🔌"
            color = "bright_yellow"
        elif event_type == "PERF":
            icon = "⏱️"
            color = "bright_cyan"

        # Use bright colors and avoid dimming too much
        self.console.print(f"[{color}]{icon} [bold]{event_type}[/bold]: {message}[/{color}]")
        if details:
            self.console.print(f"  [grey70]{details}[/grey70]")
            
        # Restart spinner
        if self.status:
            self.status.start()

# Global instance
ui = MinibotUI()
