from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Type

class BashToolInput(BaseModel):
    prompt: str = Field(description="the prompt to generate bash command for")

class BashToolResult(BaseModel):
    is_success: bool = Field(description="Indicates whether the bash command was generated successfully.")
    bash_command: str = Field(description="The generated bash command based on the prompt.")
    result: Optional[str | Dict[str, Any]] = Field(default=None, description="The result of executing the generated bash command, if applicable.")


class Base(BaseTool):
    name: str = "bash_command_generator"
    description: str = """
    generates bash commands based on user prompt.

    Use this tool to directly to any generate Linux Bash commands like: Docker build and run commands, text processing with 'cat', 'grep', 'head', 'tail', file and directory operations with 'touch', 'mkdir', 'ls', 'cd', 'mv', 'cp', 'rm' and etc.
    """
    args_schema: BashToolInput = BashToolInput()
    response_format: BashToolResult = BashToolResult()