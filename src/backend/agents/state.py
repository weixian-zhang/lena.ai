from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Annotated, List, Optional, Any, Dict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# class Agents(Enum):
#     VALUE_RESOLVER_AGENT = "ValueResolverAgent"
#     TASK_PLANNER_AGENT = "TaskPlannerAgent"
#     TASK_REFLECTION_AGENT = "TaskReflectionAgent"
#     EXECUTION_PLAN_SUPERVISOR_AGENT = "ExecutionPlanSupervisorAgent"
#     TASK_EXECUTOR_AGENT = "TaskExecutorAgent"
#     TASK_ERROR_REFLECTION_AGENT = "TaskErrorReflectionAgent"

# az cli tool
class AzureCliToolInput(BaseModel):
    prompt: str = Field(..., description="'")

class AzCliToolResult(BaseModel):
    prompt: str = Field(default='', description="'The user intent of the task to be solved by using the CLI tool.'")
    success: bool = Field(default=False, description="'Indicates whether the Azure CLI command was generated successfully.'")
    commands: list[str] = Field(default=[], description="'The list of generated Azure CLI command(s).'")
    error: str = Field(default='', description="'Error message if the command generation failed.'")

# shell tool
class AzShellToolInput(BaseModel):
    command: str = Field(description="The bash or Azure CLI command to execute.")

class AzShellToolResult(BaseModel):
    success: bool = Field(description="Indicates whether the command executed successfully.")
    stdout: Optional[str] = Field(description="The output of the executed shell command.")
    stderr: Optional[str] = Field(default=None, description="The error output of the executed shell command.")

# bash tool
class BashToolInput(BaseModel):
    prompt: str = Field(description="the prompt to generate bash command for")

class BashToolResult(BaseModel):
    is_success: bool = Field(description="Indicates whether the bash command was generated successfully.")
    commands: Optional[List[str]] = Field(description="The generated bash command based on the prompt.")
    error: Optional[str] = Field(default=None, description="The result of executing the generated bash command, if applicable.")

    
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


class Task(BaseModel):
    """
    - task_type: "az_cli" | "python", "deep_research", "bash"
    """
    task_id: str = Field(default="", description="Unique identifier for the task")
    description: str = Field(default="", description="Brief description of the task")
    task_type: Literal['az_cli', 'python', 'deep_research', 'bash'] = Field(default='az_cli'),
    tool: Optional[Tool] = Field(default=Tool(), description="The tool to be called in this step")
    az_cli_command: Optional[str] = Field(default="", description="The generated Azure CLI command(s) for this step. Empty if task is Python step")
    python: Optional[str] = Field(default="", description="The generated Python code snippet for this step. Empty if task is Azure CLI step")
    missing_parameter_context: Optional[MissingParameterContext] = Field(default=None, description="A dictionary describing what info is needed for each missing parameter")


# class MissingAzureValuesInPrompt(BaseModel):
#     missing: Optional[Any] = Field(default={}, description="The name of the missing field")
#     filled: Optional[Any] = Field(default={}, description="The filled values for the missing fields")


class TaskPlan(BaseModel):
    tasks: List[Task] = Field(default=[], description="List of tasks in the execution plan")
    
    def task_results(self) -> Dict[str, Any]:
        results = {}
        for task in self.tasks:
            if task.tool and task.tool.tool_result:
                tool_result: Dict[str, str] = task.tool.tool_result.result if task.tool.tool_result.result else {}
                results_key = task.task_id
                results[results_key] = tool_result
        return results


class ExecutionConfig:
    username: str = Field(default="", description="The username of the person initiating the agent")
    thread_id: str = Field(default="", description="The LangGraph thread id associated with this execution")
    agent_cwd: str = Field(default="", description="The current working directory for the agent")

    
class Scratchpad(BaseModel):
    """
   scratchpad used by multi-agents to record notes and observations
    """
    original_prompt: str = Field(default="", description="The prompt describing the task to be accomplished")
    resolved_prompt: str = Field(default="", description="The resolved prompt with resolved Azure resource values")
    #missing_azure_values_in_prompt: MissingAzureValuesInPrompt = Field(default=MissingAzureValuesInPrompt(), description="A dictionary containing the missing information filled in by the user")
    #notes: dict = Field(default={}, description="A dict to hold general info or observations during workflow execution")
    task_plan: TaskPlan = Field(default=TaskPlan(), description="The execution plan containing all tasks")


class ExecutionState(BaseModel):
    scratchpad: Scratchpad = Field(default=Scratchpad(), description="The scratchpad for temporary notes and observations")
    messages: Annotated[list[BaseMessage], Field(default=[], description="Conversation history"), add_messages]