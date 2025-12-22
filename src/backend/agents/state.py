from pydantic import BaseModel, Field, TypeAdapter
from typing import Literal, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import json

class Task(BaseModel):
    task_id: str = Field(default="", description="Unique identifier for the task")
    prompt: str = Field(default="", description="The prompt describing the task to be accomplished")
    type: Literal['python', 'bash', 'azcli', 'deep_research'] = Field(default='other', description="Indicates if the task involves Python code execution")
    bash_commands: List[str] = Field(default=[], description="Bash commands related to the task")
    azcli_commands: List[str] = Field(default=[], description="Azure CLI commands related to the task")
    python_code: str = Field(default="", description="Python code snippet for the task")
    output: str | dict | List[str] | None = Field(default=None, description="The output or result of the task execution")
    error: str = Field(default="", description="Error message if the task execution failed")
    is_task_successful: bool = Field(default=False, description="Indicates if the task was completed successfully")


class ToolResult(BaseModel):
    task_id: str = Field(default="", description="Unique identifier for the task")
    result: dict  | None = Field(default=None, description="The result of the action taken for the task")

class PromptAzureMissingValues(BaseModel):
    missing_values: dict = Field(default={}, description="The name of the missing field")
    filled_values: dict = Field(default={}, description="The filled values for the missing fields")

class Scratchpad(BaseModel):
    """
    - notes: a dict to hold general sensitive or non-sensitive info that does not tie to any task like SQL connection string, Azure resource ids, API keys, etc.
    - tool_results: a list of ToolResult to hold results from tool calls are specific to tasks
    """
    user_prompt: str = Field(default="", description="The original user prompt that initiated the execution")
    prompt_azure_missing_values: PromptAzureMissingValues = Field(default=PromptAzureMissingValues(), description="A dictionary containing the missing information filled in by the user")
    notes: dict = Field(default={}, description="A dict to hold general info or observations during workflow execution")
    tool_results: List[ToolResult] = Field(default=[], description="List of action results recorded in the scratch pad")
    def to_string(self) -> str:
        for ar in self.action_results:
            self.notes.update({ar.task_id: ar.result})
        return json.dumps(self.notes, indent=2)

class TaskPlan(BaseModel):
    tasks: List[Task] = Field(default=[], description="List of tasks in the execution plan")
    tool_results: List[ToolResult] = Field(default=[], description="List of action results for the tasks")


class ExecutionState(BaseModel):
    scratchpad: Scratchpad = Field(default=Scratchpad(), description="The scratchpad for temporary notes and observations")
    execution_plan: TaskPlan = Field(default=TaskPlan(), description="The execution plan containing all tasks")
    messages: Annotated[list[BaseMessage], Field(default=[], description="Conversation history"), add_messages]