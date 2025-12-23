from pydantic import BaseModel, Field, TypeAdapter
from typing import Literal, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import json

class Task(BaseModel):
    task_id: str = Field(default="", description="Unique identifier for the task")
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

class MissingAzureValuesInPrompt(BaseModel):
    missing: dict = Field(default={}, description="The name of the missing field")
    filled: dict = Field(default={}, description="The filled values for the missing fields")


class TaskPlan(BaseModel):
    tasks: List[Task] = Field(default=[], description="List of tasks in the execution plan")
    tool_results: List[ToolResult] = Field(default=[], description="List of action results for the tasks")

class Scratchpad(BaseModel):
    """
   scratchpad used by multi-agents to record notes and observations
    """
    original_prompt: str = Field(default="", description="The prompt describing the task to be accomplished")
    resolved_prompt: str = Field(default="", description="The resolved prompt with resolved Azure resource values")
    missing_azure_values_in_prompt: MissingAzureValuesInPrompt = Field(default=MissingAzureValuesInPrompt(), description="A dictionary containing the missing information filled in by the user")
    #notes: dict = Field(default={}, description="A dict to hold general info or observations during workflow execution")
    tool_results: List[ToolResult] = Field(default=[], description="List of action results recorded in the scratch pad")
    execution_plan: TaskPlan = Field(default=TaskPlan(), description="The execution plan containing all tasks")
    def to_string(self) -> str:
        for ar in self.action_results:
            self.notes.update({ar.task_id: ar.result})
        return json.dumps(self.notes, indent=2)

class ExecutionState(BaseModel):
    scratchpad: Scratchpad = Field(default=Scratchpad(), description="The scratchpad for temporary notes and observations")
    messages: Annotated[list[BaseMessage], Field(default=[], description="Conversation history"), add_messages]