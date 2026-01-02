from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Annotated, List, Optional, Any, Dict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from agents.tools.az_cli import AzCliTool, AzCliToolResult
from agents.tools.code import CodeTool, CodeToolResult
from agents.tools.bash import BashTool, BashToolResult
from agents.tools.deep_research import DeepResearchTool, DeepResearchToolResult
# class Agents(Enum):
#     VALUE_RESOLVER_AGENT = "ValueResolverAgent"
#     TASK_PLANNER_AGENT = "TaskPlannerAgent"
#     TASK_REFLECTION_AGENT = "TaskReflectionAgent"
#     EXECUTION_PLAN_SUPERVISOR_AGENT = "ExecutionPlanSupervisorAgent"
#     TASK_EXECUTOR_AGENT = "TaskExecutorAgent"
#     TASK_ERROR_REFLECTION_AGENT = "TaskErrorReflectionAgent"

# base classes
class ToolResult(BaseModel):
    is_successful: bool = Field(default=False, description="Indicates if the tool call was successful")
    error: Optional[str] = Field(default='', description="The error message if the tool call failed")

# az cli tool
class AzureCliToolInput(BaseModel):
    prompt: str = Field(..., description="'")

class AzCliToolResult(ToolResult):
    commands: list[str] = Field(default=[], description="'The list of generated Azure CLI command(s).'")

# shell tool
class AzShellToolInput(BaseModel):
    command: str = Field(description="The bash or Azure CLI command to execute.")

class AzShellToolResult(ToolResult):
    stdout: Optional[str] = Field(description="The output of the executed shell command.")
    stderr: Optional[str] = Field(default=None, description="The error output of the executed shell command.")

# bash tool
class BashToolInput(BaseModel):
    prompt: str = Field(description="the prompt to generate bash command for")

class BashToolResult(BaseModel):
    commands: Optional[List[str]] = Field(description="The generated bash command based on the prompt.")


# code tool
class CodeToolInput(BaseModel):
    prompt: str = Field(..., description="The prompt to generate code for")
    agent_cwd: Optional[str] = Field(default=None, description="The working directory for the agent to read/write files.")
    execute_code: Optional[bool] = Field(default=False, description="If true, the generated Python code will be executed.")

class CodeAgentToolCall(BaseModel):
    name: str = Field(..., description="The name of the tool called by the code agent.")
    arg: Optional[str | Any | None] = Field(default=None, description="The arguments passed to the tool.")

class CodeAgentActionStep(BaseModel):
    """
    - error: contains execution errors throughout all code execution steps.
    """
    step_number: Optional[int] = Field(default=None, description="The step number of the action step.")
    code_action: str = Field(default='', description="The code action taken by the code agent.")
    action_output: Optional[Any | None] = Field(default=None, description="The output from executing the code action.")
    observations: str | None  = Field(default=None, description="The observations from executing the code action.")
    error: Optional[str] = Field(default=None, description="Error message if the code generation or execution failed.")
    llm_output: str = Field(default='', description="The output from the model after executing the code action.")
    tool_calls: List[CodeAgentToolCall] = Field(default=[], description="All tool calls made during code generation and execution.")
    # observations_images: list[PIL.Image.Image] | None = Field(default=None, description="Any images generated during the code action execution.")
    

class CodeAgentActionOutput(BaseModel):
    """final output from the agent after executing all steps."""
    result: Any = Field(default=None, description="The final output from the code execution.")
    is_successful: bool = Field(default=False, description="Indicates whether this is the final answer from the agent.")

class CodeToolResult(ToolResult):
    messages: Optional[List] = Field(default=[], description="The messages exchanged during the code generation and execution process.")
    action_steps: Optional[List[CodeAgentActionStep]] = Field(default=[], description="All action steps taken during code generation and execution.")
    action_outputs: Optional[List[CodeAgentActionOutput]] = Field(default=[], description="The final output from the agent after executing all steps.")

    def final_result(self) -> CodeAgentActionOutput:
        result = self.action_outputs[-1] if self.action_outputs else None
        return result

    
# class ToolResult(BaseModel):
#     is_successful: bool = Field(default=False, description="Indicates if the tool call was successful")
#     result: Optional[Dict[str, str]] = Field( default={}, description="The result data from the tool call")
#     error: Optional[str] = Field(default='', description="The error message if the tool call failed")

# class Tool(BaseModel):
#     name: str = Field(default="", description="The name of the tool to be called")
#     prompt: str = Field(default="", description="The prompt to be used for the tool call")
#     tool_result: Optional[ToolResult] = Field(default=ToolResult(), description="The result of the tool call")

class TaskPlannerTaskOutput(BaseModel):
    task_id: str = Field(default="", description="Unique identifier for the task")
    description: str = Field(default="", description="Brief description of the task")
    task_type: Literal['az_cli', 'python', 'deep_research', 'bash'] = Field(default='az_cli'),
    prompt: str = Field(default="", description="The prompt describing the task to be accomplished")

class TaskPlannerOutput(BaseModel):
    tasks: List[TaskPlannerTaskOutput] = Field(default=[], description="List of planned tasks")

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
    prompt: str = Field(default="", description="The prompt describing the task to be accomplished")
    tool_result: Optional[Dict[Literal['az_cli', 'python', 'deep_research', 'bash'], ToolResult]] = Field(default={}, description="The result from the tool execution for this task")
    # az_cli_tool_result: AzCliToolResult = Field(default=AzCliToolResult(), description="Azure CLI commands from tool based on user prompt")
    # code_tool_result: CodeToolResult = Field(default=CodeToolResult(), description="python code snippet from tool based on user prompt")
    # bash_tool_result: BashToolResult = Field(default=BashToolResult(), description="bash commands from tool based on user prompt")
    # deep_research_tool_result: DeepResearchToolResult = Field(default=DeepResearchToolResult(), description="deep web research results from tool based on user query")
    # tool: Optional[Tool] = Field(default=Tool(), description="The tool to be called in this step")
    # az_cli_command: Optional[str] = Field(default="", description="The generated Azure CLI command(s) for this step. Empty if task is Python step")
    # python: Optional[str] = Field(default="", description="The generated Python code snippet for this step. Empty if task is Azure CLI step")
    missing_parameter_context: Optional[MissingParameterContext] = Field(default=None, description="A dictionary describing what info is needed for each missing parameter")


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


class ExecutionConfig(BaseModel):
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
    execution_config: ExecutionConfig = Field(default=ExecutionConfig(), description="The configuration for the current execution")
    scratchpad: Scratchpad = Field(default=Scratchpad(), description="The scratchpad for temporary notes and observations")
    messages: Annotated[list[BaseMessage], Field(default=[], description="Conversation history"), add_messages]