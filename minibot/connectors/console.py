from .base import BaseConnector
from ..ui import ui  # Import the new UI system

class ConsoleConnector(BaseConnector):
    """Handles input/output via the command line with Rich UI."""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def start(self):
        ui.display_welcome()
        print("\nType 'exit' or 'quit' to stop.\n")
        
        while True:
            try:
                # Use Rich's prompt (simulated)
                # Note: Prompt.ask handles basic input. 
                # For async input handling in a real loop, we might need a separate thread or just use input()
                # To keep it simple and compatible with existing structure:
                user_input = input("\n👤 You: ")
                
                if user_input.lower() in ["exit", "quit"]:
                    print("Goodbye!")
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
                print(f"\n🤖 Minibot: {response}")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                ui.stop_thinking()
                print(f"Error: {e}")
