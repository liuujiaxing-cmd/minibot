from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status
from rich.prompt import Prompt
from rich.table import Table
from rich import box
from datetime import datetime

console = Console()

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
            f"[bold cyan]{title}[/bold cyan]\n[dim]v2.0 - Cognitive Agent with Plugin System[/dim]",
            box=box.DOUBLE,
            border_style="cyan"
        ))

    def get_user_input(self) -> str:
        """Get input with styling."""
        return Prompt.ask("\n[bold green]You[/bold green]")

    def display_assistant_response(self, text: str):
        """Render AI response as Markdown."""
        self.console.print("\n[bold purple]Minibot[/bold purple]")
        self.console.print(Markdown(text))

    def start_thinking(self, message="Thinking..."):
        """Start a spinner."""
        if self.status:
            self.status.stop()
        self.status = self.console.status(f"[yellow]{message}[/yellow]", spinner="dots")
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
        color = "white"
        
        if event_type == "TOOL":
            icon = "🛠️"
            color = "blue"
        elif event_type == "SAFETY":
            icon = "🛡️"
            color = "green"
        elif event_type == "PLAN":
            icon = "📝"
            color = "magenta"
        elif event_type == "MEMORY":
            icon = "🧠"
            color = "cyan"
        elif event_type == "ERROR":
            icon = "❌"
            color = "red"

        self.console.print(f"[{color}]{icon} [bold]{event_type}[/bold]: {message}[/{color}]")
        if details:
            self.console.print(f"  [dim]{details}[/dim]")
            
        # Restart spinner
        if self.status:
            self.status.start()

# Global instance
ui = MinibotUI()
