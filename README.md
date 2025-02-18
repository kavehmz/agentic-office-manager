# Agentic Office Manager

An intelligent Slack bot powered by LangChain that serves as an office manager, capable of executing various tools and functions with built-in approval workflows.

## Overview

This project implements a Slack bot that uses Large Language Models (LLMs) to understand and respond to user requests. It features a sophisticated system for managing conversations, executing tools, and handling function approvals in a thread-based context.

## Features

- 🤖 AI-powered Slack bot using LangChain
- 🧵 Thread-based conversation management
- ✅ Built-in approval workflow for sensitive operations
- 🔧 Extensible tool system
- 🔒 Environment-based configuration
- 📝 Comprehensive logging

## Prerequisites

- Python 3.x
- Slack App with Socket Mode enabled
- OpenAI API key (or other supported LLM provider)

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install slack-bolt python-dotenv langchain
   ```

3. Set up your Slack App:
   - Create a new Slack App in your workspace
   - Enable Socket Mode in your Slack App settings
   - Generate an App-Level Token with `connections:write` scope
   - Add bot token scopes: `app_mentions:read`, `chat:write`, `im:history`
   - Install the app to your workspace

4. Create a `.env` file based on `.env.example` with the following variables:
   ```
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_APP_TOKEN=xapp-your-app-token
   MODEL_NAME=gpt-4  # or your preferred model
   MODEL_PROVIDER=openai  # or your preferred provider
   ```

## Running the Bot

### Slack Interface

1. Start the Slack bot:
   ```bash
   python slack.py
   ```

2. The bot will connect to Slack using Socket Mode, which:
   - Provides a secure connection without exposing public endpoints
   - Eliminates the need for setting up SSL/TLS certificates
   - Works behind firewalls and in local development
   - Enables real-time message handling

3. Once connected, you can interact with the bot by:
   - Mentioning it in a channel: `@YourBot hello`
   - The bot will respond in a thread
   - All subsequent messages in the thread will be processed by the bot

### CLI Interface (Local Testing)

The project includes a CLI interface specifically designed for local testing and development:

1. Start the CLI interface:
   ```bash
   python cli.py
   ```

2. This testing interface provides:
   - Local interaction without needing Slack
   - Quick testing of new tools and features
   - Direct feedback for development
   - Tool approval workflow testing
   - Command history for repeated testing scenarios

3. Testing commands:
   - `help`: Show available commands
   - `exit` or `quit`: End the session
   - Any other input will be processed by the AI assistant

The CLI interface is particularly useful for:
- Developing and testing new tools
- Debugging tool approval workflows
- Verifying AI responses locally
- Quick iterations during development

## Project Structure

- `slack.py` - Main Slack bot implementation with message handling and interactive components
- `manager.py` - Conversation management and LLM integration
- `tools.py` - Tool definitions and implementations
- `system.md` - System prompt for the AI agent

## Tools System

The bot uses a flexible tool system that allows it to perform specific actions based on user requests. Tools are Python functions that can be called by the AI to perform tasks.

### Tool Concepts

1. **Tool Definition**
   - Tools are Python functions decorated with `@tool`
   - Each tool must have a clear docstring describing its purpose
   - Tools can accept parameters and must return a result
   - Tools have access to injected arguments via `InjectedToolArg`

2. **Tool Types**
   - **Standard Tools**: Basic functions that don't require approval
   - **Approval-Required Tools**: Functions that need user confirmation before execution
   - **System Tools**: Internal functions for bot management

### Tool Workflow

1. **Execution Flow**
   - AI model identifies the need for a tool
   - Tool is called with appropriate parameters
   - Result is processed and returned to the conversation

2. **Approval Process**
   - Tools marked with `@requires_approval` trigger approval flow
   - Interactive buttons appear in Slack
   - Tool executes only after user approval

### Adding New Tools

1. **Basic Tool Creation**
   ```python
   @enabled_tool
   @tool
   def your_tool(param: str, opts: Annotated[dict, InjectedToolArg]) -> str:
       """
       Clear description of what the tool does.
       
       Args:
           param: Description of the parameter
           opts: Injected options dictionary
       
       Returns:
           Description of the return value
       """
       return result
   ```

2. **Adding Approval Requirement**
   ```python
   @requires_approval
   @enabled_tool
   @tool
   def sensitive_tool(param: str, opts: Annotated[dict, InjectedToolArg]) -> str:
       """Tool that requires approval before execution"""
       return result
   ```

3. **Best Practices**
   - Write clear docstrings
   - Handle errors gracefully
   - Return meaningful results
   - Consider security implications
   - Add logging for debugging

## System Prompt (system.md)

The `system.md` file is a crucial component that defines the bot's personality, capabilities, and behavioral guidelines.

### Purpose

1. **Identity Definition**
   - Sets the bot's role and personality
   - Defines interaction style
   - Establishes behavioral boundaries

2. **Capability Configuration**
   - Lists available tools and their proper usage
   - Defines decision-making guidelines
   - Sets response formatting rules

3. **Context Setting**
   - Provides background knowledge
   - Defines operational context
   - Sets up error handling procedures

### Writing Guidelines

1. **Structure**
   ```markdown
   # Role and Identity
   [Define who the bot is and its primary purpose]

   # Capabilities
   [List what the bot can and cannot do]

   # Interaction Guidelines
   [Define how the bot should interact]

   # Tool Usage
   [Explain when and how to use tools]

   # Response Formatting
   [Define how responses should be structured]
   ```

2. **Best Practices**
   - Be clear and specific
   - Use examples for complex concepts
   - Define boundaries explicitly
   - Include error handling guidelines
   - Specify response formats

3. **Important Elements**
   - Clear role definition
   - Tool usage guidelines
   - Response formatting rules
   - Error handling procedures
   - Ethical guidelines

## Error Handling

The system includes comprehensive error handling:
- Logging of all operations and errors
- Graceful error messages in Slack
- Thread-based error containment

## Security Considerations

- Function approval workflow for sensitive operations
- Environment-based configuration
- Thread isolation for conversations
- Token-based authentication for Slack

## Logging

The system uses Python's built-in logging module with:
- Timestamp
- Log level
- Component name
- Detailed message

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
