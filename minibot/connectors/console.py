from .base import BaseConnector
from ..ui import ui  # Import the new UI system

class ConsoleConnector(BaseConnector):
    """Handles input/output via the command line with Rich UI."""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def start(self):
        ui.display_welcome()
        ui.console.print("\nType 'exit' or 'quit' to stop.\n", style="bold bright_white")
        
        while True:
            try:
                # Use Rich's prompt via UI system for consistent styling
                user_input = ui.get_user_input()
                
                if user_input.lower() in ["exit", "quit"]:
                    ui.console.print("Goodbye!", style="bold bright_white")
                    break
                
                if not user_input.strip():
                    continue
                
                # Start thinking UI
                ui.start_thinking()
                
                # Process message
                response = await self.agent.process_message(user_input)
                
                # Stop thinking UI
                ui.stop_thinking()
                
                # Display response
                ui.display_assistant_response(response)
                
            except KeyboardInterrupt:
                ui.console.print("\nGoodbye!", style="bold bright_white")
                break
            except Exception as e:
                ui.stop_thinking()
                ui.log_event("ERROR", str(e))
