#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import logging
from manager import LangGraphManager
import sys
import readline  # Enables arrow key navigation and command history

# Load environment variables from .env file
load_dotenv()

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CliInterface:
    def __init__(self):
        self.manager = LangGraphManager()
        self.conversation_id = "cli_session"
        logger.info("CLI interface initialized")

    def handle_approval(self, response: str, tool_info: dict) -> None:
        """Handle approval requests for tools."""
        if tool_info and "pending_tool_calls" in tool_info:
            print("\nApproval Required:")
            print(response)
            print("\nTool Calls:")
            for tool_call in tool_info["pending_tool_calls"]:
                print(f"\nFunction: {tool_call['name']}")
                print(f"Arguments: {tool_call['arguments']}")
            
            while True:
                choice = input("\nDo you approve this action? (y/n): ").lower()
                if choice in ['y', 'n']:
                    break
                print("Please enter 'y' for yes or 'n' for no.")

            approved = choice == 'y'
            response, new_tool_info = self.manager.process_message(
                text="",
                conversation_id=self.conversation_id,
                approved_functions=approved
            )
            print(f"\n{response}")

    def run(self):
        """Run the CLI interface."""
        print("Welcome to the Office Manager CLI!")
        print("Type 'exit' or 'quit' to end the session.")
        print("Type 'help' for available commands.")
        
        while True:
            try:
                # Get user input
                user_input = input("\n> ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                # Check for help command
                if user_input.lower() == 'help':
                    print("\nAvailable Commands:")
                    print("- help: Show this help message")
                    print("- exit/quit: End the session")
                    print("- Any other input will be processed by the AI assistant")
                    continue
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Process the message
                response, tool_info = self.manager.process_message(
                    text=user_input,
                    conversation_id=self.conversation_id
                )
                
                # Handle approval if needed
                if tool_info and "pending_tool_calls" in tool_info:
                    self.handle_approval(response, tool_info)
                else:
                    print(f"\n{response}")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error processing input: {str(e)}", exc_info=True)
                print(f"\nError: {str(e)}")

def main():
    """Main entry point for the CLI interface."""
    try:
        cli = CliInterface()
        cli.run()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
