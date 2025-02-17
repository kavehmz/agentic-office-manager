from typing import Dict, Any, List, Tuple
import logging
import os
import os.path
logger = logging.getLogger(__name__)
from langchain.chat_models import init_chat_model

from tools import (
    NEEDS_APPROVAL,
    AVAILABLE_TOOLS,
    TOOL_MAP
)

def get_llm_model() -> Any:
    """Get the appropriate LLM model based on environment variables."""
    model_name = os.getenv('MODEL_NAME', 'gpt-4o')
    model_provider = os.getenv('MODEL_PROVIDER', 'openai')
    return init_chat_model(
        model_name,
        model_provider=model_provider,
        max_tokens=1024*8
    )

class LangGraphManager:
    def __init__(self):
        self.external_params = {"age": 2}
        self.model = Any
        self.messages = []
        self.approval_message_ts = ""
        self.pendig_approval = None
        self._create_agent()
        logger.info("Initialized LangGraphManager with external_params: %s", self.external_params)
        
    def _create_agent(self) -> Any:
        llm = get_llm_model()
        self.model = llm.bind_tools(AVAILABLE_TOOLS)
        
        # Read system message from system.md file
        system_path = os.path.join(os.path.dirname(__file__), 'system.md')
        system_message = "You are called Batman"
        try:
            with open(system_path, 'r') as f:
                system_message = f.read()
        except FileNotFoundError:
            logger.info("could not load : %s", system_path)
            
        self.messages = [
            (
                "system",
                system_message
            )
        ]

    def ask_for_approval(self, tool_calls: List[Dict]) -> tuple[str, Dict]:
        """Create a json for name and arguments for the tool calls."""
        tool_info = []
        for tool_call in tool_calls:
            tool_info.append({
                "name": tool_call["name"],
                "arguments": tool_call["args"]
            })
        return "", {"pending_tool_calls": tool_info}

    def _execute_tool_calls(self, tool_calls: List[Dict], approved: bool = False) -> List[Dict]:
        """Execute tool calls and return their messages."""
        tool_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"].lower()
            if NEEDS_APPROVAL.get(tool_name, False) and not approved:
                # Create a rejection message
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", "unknown"),
                    "name": tool_name,
                    "content": "User rejected your request to run the function. Consider our options or discuss the matter with the user."
                })
            else:
                selected_tool = TOOL_MAP[tool_name]
                tool_call["args"].update({"opts": self.external_params})
                tool_msg = selected_tool.invoke(tool_call)
                tool_messages.append(tool_msg)
        return tool_messages

    def process_message(self, text: str, conversation_id: str, approved_functions: bool = False) -> Tuple[str, Dict[str, Any]]:
        """Process a message using the provided agent."""
        logger.info("Processing message for conversation_id: %s", conversation_id)
        logger.info("Input text: %s", text)
        try:
            # Check for pending approvals first
            if hasattr(self, 'pendig_approval') and self.pendig_approval:
                if approved_functions:
                    # Execute pending tool calls with approval
                    tool_messages = self._execute_tool_calls(self.pendig_approval, approved=True)
                    for msg in tool_messages:
                        self.messages.append(msg)
                    self.pendig_approval = None
                else:
                    # Reject all pending tool calls
                    tool_messages = self._execute_tool_calls(self.pendig_approval, approved=False)
                    for msg in tool_messages:
                        self.messages.append(msg)
                    self.pendig_approval = None
                
                # # Continue with normal processing after handling pending approvals
                # ai_msg = self.model.invoke(self.messages)
                # self.messages.append(ai_msg)
                # print(ai_msg)
                # return ai_msg.content, {}
            else:
                # Normal message processing
                user_message = {"role": "user", "content": text}
                self.messages.append(user_message)

            while True:
                ai_msg = self.model.invoke(self.messages)
                self.messages.append(ai_msg)
                
                if not ai_msg.tool_calls:
                    return ai_msg.content, {}

                needs_approval = False
                for tool_call in ai_msg.tool_calls:
                    tool_name = tool_call["name"].lower()
                    if NEEDS_APPROVAL.get(tool_name, False):
                        needs_approval = True
                        break

                if needs_approval:
                    self.pendig_approval = ai_msg.tool_calls
                    return self.ask_for_approval(ai_msg.tool_calls)

                # Execute tool calls without approval needed
                tool_messages = self._execute_tool_calls(ai_msg.tool_calls)
                for msg in tool_messages:
                    self.messages.append(msg)

        except Exception as e:
            logger.error("Error processing message: %s", str(e), exc_info=True)
            raise

# Dictionary to store LangGraphManager instances per conversation
conversation_managers: Dict[str, LangGraphManager] = {}

def get_manager(conversation_id: str) -> LangGraphManager:
    """Get an existing manager or create a new one for the given conversation ID."""
    return conversation_managers[conversation_id]


def get_or_create_manager(conversation_id: str) -> LangGraphManager:
    """Get an existing manager or create a new one for the given conversation ID."""
    if conversation_id not in conversation_managers:
        conversation_managers[conversation_id] = LangGraphManager()
    return conversation_managers[conversation_id]
