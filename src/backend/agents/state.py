from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Annotated, List, Optional, Any, Dict
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

class ToolResult(BaseModel):
    is_successful: bool = Field(default=False, description="Indicates if the tool call was successful")
    result: Optional[Dict[str, str]] = Field( default={}, description="The result data from the tool call")
    error: Optional[str] = Field(default='', description="The error message if the tool call failed")

class Tool(BaseModel):
    name: str = Field(default="", description="The name of the tool to be called")
    prompt: str = Field(default="", description="The prompt to be used for the tool call")
    tool_result: Optional[ToolResult] = Field(default=ToolResult(), description="The result of the tool call")

class MissingParameters(BaseModel):
    name: str = Field(default="", description="The name of the missing parameter")
    value: Optional[str] = Field(default=None, description="The value provided for the missing parameter")
    reference_data: Optional[str] = Field(default="", description="Reference data or description for the missing parameter")


class MissingParameterContext(BaseModel):
    task_id: str = Field(default="", description="The ID of the task this missing parameter belongs to")
    step_id: str = Field(default=0.0, description="The ID of the step this missing parameter belongs to")
    missing_parameters: List[MissingParameters] = Field(default=[], description="List of missing parameters for this step")
    

# class Step(BaseModel):
#     step_id: str = Field(default="", description="Unique identifier for the step within the task")
#     description: str = Field(default="", description="Brief description of what this step does")
#     task_type: Literal['az_cli', 'python', 'deep_research'] = Field(default='az_cli'),
#     tool: Optional[Tool] = Field(default=Tool(), description="The tool to be called in this step")
#     az_cli_command: Optional[str] = Field(default="", description="The generated Azure CLI command(s) for this step. Empty if task is Python step")
#     python: Optional[str] = Field(default="", description="The generated Python code snippet for this step. Empty if task is Azure CLI step")
#     missing_parameter_context: Optional[MissingParameterContext] = Field(default=None, description="A dictionary describing what info is needed for each missing parameter")

class Task(BaseModel):
    task_id: str = Field(default="", description="Unique identifier for the task")
    description: str = Field(default="", description="Brief description of the task")
    task_type: Literal['az_cli', 'python', 'deep_research'] = Field(default='az_cli'),
    tool: Optional[Tool] = Field(default=Tool(), description="The tool to be called in this step")
    az_cli_command: Optional[str] = Field(default="", description="The generated Azure CLI command(s) for this step. Empty if task is Python step")
    python: Optional[str] = Field(default="", description="The generated Python code snippet for this step. Empty if task is Azure CLI step")
    missing_parameter_context: Optional[MissingParameterContext] = Field(default=None, description="A dictionary describing what info is needed for each missing parameter")


# class MissingAzureValuesInPrompt(BaseModel):
#     missing: Optional[Any] = Field(default={}, description="The name of the missing field")
#     filled: Optional[Any] = Field(default={}, description="The filled values for the missing fields")


class TaskPlan(BaseModel):
    tasks: List[Task] = Field(default=[], description="List of tasks in the execution plan")
    
    def tool_results(self) -> Dict[str, Any]:
        results = {}
        for task in self.tasks:
            for step in task.steps:
                if step.tool and step.tool.tool_result:
                    results_key = f"task_{task.task_id}_step_{step.step_id}"
                    results[results_key] = step.tool.tool_result
        return results

class Scratchpad(BaseModel):
    """
   scratchpad used by multi-agents to record notes and observations
    """
    original_prompt: str = Field(default="", description="The prompt describing the task to be accomplished")
    resolved_prompt: str = Field(default="", description="The resolved prompt with resolved Azure resource values")
    #missing_azure_values_in_prompt: MissingAzureValuesInPrompt = Field(default=MissingAzureValuesInPrompt(), description="A dictionary containing the missing information filled in by the user")
    #notes: dict = Field(default={}, description="A dict to hold general info or observations during workflow execution")
    execution_plan: TaskPlan = Field(default=TaskPlan(), description="The execution plan containing all tasks")


class ExecutionState(BaseModel):
    username: str = Field(default="", description="The username of the person initiating the agent")
    thread_id: str = Field(default="", description="The LangGraph thread id associated with this execution")
    agent_cwd = Field(default="", description="The current working directory for the agent")
    scratchpad: Scratchpad = Field(default=Scratchpad(), description="The scratchpad for temporary notes and observations")
    messages: Annotated[list[BaseMessage], Field(default=[], description="Conversation history"), add_messages]