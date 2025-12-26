from pydantic import BaseModel, Field, TypeAdapter
from typing import Literal, Annotated, List, Optional, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import json
from enum import Enum

class Agents(Enum):
    VALUE_RESOLVER_AGENT = "ValueResolverAgent"
    TASK_PLANNER_AGENT = "TaskPlannerAgent"
    TASK_REFLECTION_AGENT = "TaskReflectionAgent"
    EXECUTION_PLAN_SUPERVISOR_AGENT = "ExecutionPlanSupervisorAgent"
    TASK_EXECUTOR_AGENT = "TaskExecutorAgent"
    TASK_ERROR_REFLECTION_AGENT = "TaskErrorReflectionAgent"

class Tool(BaseModel):
    name: str = Field(default="", description="The name of the tool to be called")
    prompt: str = Field(default="", description="The prompt to be used for the tool call")


class StepMissingParameters(BaseModel):
    parameter_name: str = Field(default="", description="The name of the missing parameter")
    reference_data: Optional[str] = Field(default="", description="Reference data or description for the missing parameter")

class Step(BaseModel):
    step_id: float = Field(default="", description="Unique identifier for the step within the task")
    description: str = Field(default="", description="Brief description of what this step does")
    task_type: Literal['az_cli', 'python', 'deep_research'] = Field(default='az_cli'),
    tool_prompt: str = Field(default="", description="The prompt to be used for the tool call in this step")
    tool: Optional[Tool] = Field(default=Tool(), description="The tool to be called in this step")
    tool_result: Optional[Any] = Field(default=None, description="The result of the tool call")
    tool_error: Optional[Any] = Field(default=None, description="The error message if the tool call failed")
    is_tool_call_successful: bool = Field(default=False, description="Indicates if the tool call was successful")
    az_cli_command: Optional[str] = Field(default="", description="The generated Azure CLI command(s) for this step. Empty if task is Python step")
    python: Optional[str] = Field(default="", description="The generated Python code snippet for this step. Empty if task is Azure CLI step")
    missing_parameters: Optional[dict] = Field(default={}, description="A dictionary describing what info is needed for each missing parameter")

class Task(BaseModel):
    task_id: str = Field(default="", description="Unique identifier for the task")
    description: str = Field(default="", description="Brief description of the task")
    steps: List[Step] = Field(default=[], description="List of steps in the task")


class MissingAzureValuesInPrompt(BaseModel):
    missing: dict = Field(default={}, description="The name of the missing field")
    filled: dict = Field(default={}, description="The filled values for the missing fields")


class TaskPlan(BaseModel):
    tasks: List[Task] = Field(default=[], description="List of tasks in the execution plan")

class Scratchpad(BaseModel):
    """
   scratchpad used by multi-agents to record notes and observations
    """
    original_prompt: str = Field(default="", description="The prompt describing the task to be accomplished")
    resolved_prompt: str = Field(default="", description="The resolved prompt with resolved Azure resource values")
    missing_azure_values_in_prompt: MissingAzureValuesInPrompt = Field(default=MissingAzureValuesInPrompt(), description="A dictionary containing the missing information filled in by the user")
    #notes: dict = Field(default={}, description="A dict to hold general info or observations during workflow execution")
    execution_plan: TaskPlan = Field(default=TaskPlan(), description="The execution plan containing all tasks")
    def to_string(self) -> str:
        for ar in self.action_results:
            self.notes.update({ar.task_id: ar.result})
        return json.dumps(self.notes, indent=2)

class ExecutionState(BaseModel):
    scratchpad: Scratchpad = Field(default=Scratchpad(), description="The scratchpad for temporary notes and observations")
    messages: Annotated[list[BaseMessage], Field(default=[], description="Conversation history"), add_messages]