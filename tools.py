from typing import Dict, Any
from langchain_core.tools import tool, InjectedToolArg
from typing_extensions import Annotated
from datetime import datetime

NEEDS_APPROVAL = {}

def requires_approval(func):
    NEEDS_APPROVAL[func.__name__] = True
    return func

AVAILABLE_TOOLS = []

def enabled_tool(func):
    AVAILABLE_TOOLS.append(func)
    return func

@enabled_tool
@tool
@requires_approval
def random_string(random_number: int, opts: Annotated[dict, InjectedToolArg]) -> str:
    """Whenever user is asking for a random string you call this function and pass a random number as the seed"""
    print("called: " + "random_string")
    return "RaNdOm124" * opts["age"]

@enabled_tool
@tool
def to_upper(input_text: str, opts: Annotated[dict, InjectedToolArg]) -> str:
    """This function will convert the input_text to all upper case"""
    print("called: " + "to_upper")
    return input_text.upper()

@enabled_tool
@tool
def get_date(opts: Annotated[dict, InjectedToolArg]) -> str:
    """Returns the current date as a string in the format YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

# Create a dictionary mapping tool names to tool functions
TOOL_MAP = {tool.name.lower(): tool for tool in AVAILABLE_TOOLS}
