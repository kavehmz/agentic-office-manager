import os
from dotenv import load_dotenv
from slack_bolt import App

# Load environment variables from .env file
load_dotenv()
from slack_bolt.adapter.socket_mode import SocketModeHandler
from typing import Dict, List, Any
from manager import get_or_create_manager, get_manager, conversation_managers
import logging
from datetime import datetime

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def bot_man(text: str, conversation_history_id: str, say, thread_ts: str, approved_functions: bool = False, call_from_button: bool = False) -> None:
    """Process a message using the LangGraph agent and handle Slack interactions."""
    logger.info("bot_man called with conversation_history_id: %s, approved_functions: %s",
                conversation_history_id, approved_functions)
    
    try:
        manager = get_manager(conversation_history_id)
        response = None
        tool_info = None

        # Check for pending approvals first
        if hasattr(manager, 'pendig_approval') and manager.pendig_approval:
            if approved_functions:
                # Execute pending approvals and get new state
                response, tool_info = manager.process_message(
                    text="",
                    conversation_id=conversation_history_id,
                    approved_functions=True
                )
            else:
                # Reject pending approvals and get new state
                response, tool_info = manager.process_message(
                    text="",
                    conversation_id=conversation_history_id,
                    approved_functions=False
                )
        else:
            # Process new message
            response, tool_info = manager.process_message(
                text=text,
                conversation_id=conversation_history_id,
                approved_functions=False
            )

        logger.info("Message processed successfully, response: %s, tool_info: %s", response, tool_info)

        # Handle response based on tool_info state
        if tool_info and "pending_tool_calls" in tool_info:
            # New approval needed, create approval message
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Approval Required*\n{response}"
                    }
                }
            ]
            
            # Add tool call information
            for tool_call in tool_info["pending_tool_calls"]:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Function:* {tool_call['name']}\n*Arguments:* ```{tool_call['arguments']}```"
                    }
                })
            
            # Add approval buttons
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Approve"
                        },
                        "style": "primary",
                        "value": conversation_history_id,
                        "action_id": "approve_function"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Cancel"
                        },
                        "style": "danger",
                        "value": conversation_history_id,
                        "action_id": "cancel_function"
                    }
                ]
            })
            
            # Send message and store the response which contains the message timestamp
            approval_text = f"Approval Required: {response}"
            result = say(blocks=blocks, text=approval_text, thread_ts=thread_ts)
            # Store the message ts in the manager for later updates
            manager.approval_message_ts = result['ts']
        else:
            # No approval needed, just send the response
            # Ensure there's always a text value, use a default if response is None
            text_response = response if response else "Processing your request..."
            say(text=text_response, thread_ts=thread_ts)
        
    except Exception as e:
        logger.error("Error in bot_man: %s", str(e), exc_info=True)
        say(text=f"Sorry, I encountered an error: {str(e)}", thread_ts=thread_ts)
        raise

@app.event("message")
def handle_message(event, say, client):
    """Handle all messages, including mentions and thread replies."""
    logger.info("Received message event: %s", event)
    try:
        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts", event.get("ts"))
        conversation_history_id = channel_id + "::" + thread_ts
        text = event.get("text", "")
        
        # Get app's user ID
        app_id = app.client.auth_test()["user_id"]
        logger.info("Bot app_id: %s", app_id)

        # Check if message in the channel is directed to the app
        if not event.get("thread_ts") and f"<@{app_id}>" not in text:
            logger.info("Message not directed to bot, ignoring")
            return

        # Check if this is a thread message
        if event.get("thread_ts") and conversation_history_id not in conversation_managers:
            logger.info("Thread unknown or unrelated")
            return
        
        manager = get_or_create_manager(conversation_history_id)
        if manager.approval_message_ts:
            app.client.chat_update(
                channel=channel_id,
                ts=manager.approval_message_ts,
                text="Function Cancelled",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "❌ *Function Cancelled*"
                    }
                }]
            )

        logger.info("Processing message in conversation: %s", conversation_history_id)
        bot_man(text, conversation_history_id, say, thread_ts)
        logger.info("Message processed by bot_man")
            
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        say(text="Sorry, I encountered an error processing your message.", thread_ts=thread_ts)

@app.action("approve_function")
def handle_approval(ack, body, say):
    """Handle approval button click."""
    try:
        ack()
        conversation_history_id = body["actions"][0]["value"]
        thread_ts = body["message"]["thread_ts"]
        logger.info("Function approval received for conversation: %s", conversation_history_id)
        
        # Get the original message timestamp
        message_ts = body["message"]["ts"]
        # Update the original message to show approval
        app.client.chat_update(
            channel=body["channel"]["id"],
            ts=message_ts,
            text="Function Approved and Executed",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✅ *Function Approved and Executed*"
                }
            }]
        )
        manager = get_manager(conversation_history_id)
        if manager.approval_message_ts:
            manager.approval_message_ts = ""
        # Process the approval
        bot_man("", conversation_history_id, say, thread_ts, approved_functions=True, call_from_button=True)
        
    except Exception as e:
        logger.error(f"Error handling approval: {str(e)}")
        say(text="Sorry, I encountered an error processing the approval.",
            thread_ts=body["message"]["thread_ts"])

@app.action("cancel_function")
def handle_cancellation(ack, body, say):
    """Handle cancellation button click."""
    try:
        ack()
        conversation_history_id = body["actions"][0]["value"]
        thread_ts = body["message"]["thread_ts"]
        logger.info("Function cancellation received for conversation: %s", conversation_history_id)
        
        # Get the original message timestamp
        message_ts = body["message"]["ts"]
        # Update the original message to show cancellation
        app.client.chat_update(
            channel=body["channel"]["id"],
            ts=message_ts,
            text="Function Cancelled",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "❌ *Function Cancelled*"
                }
            }]
        )
        manager = get_manager(conversation_history_id)
        if manager.approval_message_ts:
            manager.approval_message_ts = ""
        # Process the cancellation
        bot_man("", conversation_history_id, say, thread_ts, approved_functions=False, call_from_button=True)
        
    except Exception as e:
        logger.error(f"Error handling cancellation: {str(e)}")
        say(text="Sorry, I encountered an error processing the cancellation.",
            thread_ts=body["message"]["thread_ts"])

def main():
    """Main entry point for the Slack bot."""
    handler = SocketModeHandler(
        app=app,
        app_token=os.environ.get("SLACK_APP_TOKEN")
    )
    logger.info("⚡️ Bolt app is running!")
    handler.start()

if __name__ == "__main__":
    main()
