from pydantic import BaseModel, Field
from typing import Literal, Annotated, List, Optional, Any, Dict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

import os, sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

class TaskType:
    AZ_CLI = 'az_cli'
    PYTHON = 'python'  
    DEEP_RESEARCH = 'deep_research'
    BASH = 'bash'


###### base classes
class ToolResult(BaseModel):
    is_successful: bool = Field(default=False, description="Indicates if the tool call was successful")
    error: Optional[str] = Field(default='', description="The error message if the tool call failed")

###### az cli tool
class AzureCliToolInput(BaseModel):
    prompt: str = Field(..., description="'")

class AzCliToolCodeResult(ToolResult):
    commands: list[str] = Field(default=[], description="'The list of generated Azure CLI command(s).'")

###### shell tool
class AzShellToolInput(BaseModel):
    command: str = Field(description="The bash or Azure CLI command to execute.")

class AzShellToolExecutionResult(ToolResult):
    '''
    stderr will be in ToolResult.error
    '''
    stdout: Optional[str] = Field(default='', description="The output of the executed shell command.")
    #stderr: Optional[str] = Field(default=None, description="The error output of the executed shell command.")

###### bash tool
class BashToolInput(BaseModel):
    prompt: str = Field(default='', description="the prompt to generate bash command for")

class BashToolCodeResult(ToolResult):
    commands: Optional[List[str]] = Field(default=[], description="The generated bash command based on the prompt.")


###### code tool
class CodeToolInput(BaseModel):
    prompt: str = Field(default='', description="The prompt to generate code for")
    agent_cwd: Optional[str] = Field(default='', description="The working directory for the agent to read/write files.")
    execute_code: Optional[bool] = Field(default=False, description="If true, the generated Python code will be executed.")

class CodeAgentToolCall(BaseModel):
    name: str = Field(default='', description="The name of the tool called by the code agent.")
    arg: Optional[str | Any | None] = Field(default='', description="The arguments passed to the tool.")

class CodeAgentActionStep(BaseModel):
    """
    - error: contains execution errors throughout all code execution steps.
    """
    step_number: Optional[int] = Field(default=-1, description="The step number of the action step.")
    code_action: str = Field(default='', description="The code action taken by the code agent.")
    action_output: Optional[Any | None] = Field(default={}, description="The output from executing the code action.")
    observations: str | None  = Field(default='', description="The observations from executing the code action.")
    error: Optional[str] = Field(default='', description="Error message if the code generation or execution failed.")
    llm_output: str = Field(default='', description="The output from the model after executing the code action.")
    tool_calls: List[CodeAgentToolCall] = Field(default=[], description="All tool calls made during code generation and execution.")
    # observations_images: list[PIL.Image.Image] | None = Field(default=None, description="Any images generated during the code action execution.")
    

class CodeAgentActionOutput(BaseModel):
    """final output from the agent after executing all steps."""
    result: Any = Field(default={}, description="The final output from the code execution.")
    is_successful: bool = Field(default=False, description="Indicates whether this is the final answer from the agent.")


class CodeToolExecutionResult(ToolResult):
    messages: Optional[List] = Field(default=[], description="The messages exchanged during the code generation and execution process.")
    action_steps: Optional[List[CodeAgentActionStep]] = Field(default=[], description="All action steps taken during code generation and execution.")
    action_outputs: Optional[List[CodeAgentActionOutput]] = Field(default=[], description="The final output from the agent after executing all steps.")
    result: Optional[CodeAgentActionOutput] = Field(default=CodeAgentActionOutput(), description="The final result from the code tool execution.")
    

###### deep research tool
class DeepResearchToolInput(BaseModel):
    query: str = Field(default='', description="The user query for deep web research.")

class DeepResearchToolExecutionResult(ToolResult):  
    result: str = Field(default='', description="The result of the deep web research.")


class TaskPlannerTaskOutput(BaseModel):
    task_id: str = Field(default="", description="Unique identifier for the task")
    description: str = Field(default="", description="Brief description of the task")
    task_type: str = Field(default='az_cli', description="The type of task: az_cli, python, deep_research, bash")   
    prompt: str = Field(default="", description="The prompt describing the task to be accomplished")

class TaskPlannerOutput(BaseModel):
    tasks: List[TaskPlannerTaskOutput] = Field(default=[], description="List of planned tasks")

class MissingParameters(BaseModel):
    name: str = Field(default="", description="The name of the missing parameter")
    value: Optional[str] = Field(default=None, description="The value provided for the missing parameter")
    reference_data: Optional[str] = Field(default="", description="Reference data or description for the missing parameter")


# class MissingParameterContext(BaseModel):
#     task_id: str = Field(default="", description="The ID of the task this missing parameter belongs to")
#     step_id: str = Field(default=0.0, description="The ID of the step this missing parameter belongs to")
#     missing_parameters: List[MissingParameters] = Field(default=[], description="List of missing parameters for this step")


##### task states
class Task(BaseModel):
    """
    - task_type: "az_cli" | "python", "deep_research", "bash"
    """
    task_id: str = Field(default="", description="Unique identifier for the task")
    description: str = Field(default="", description="Brief description of the task")
    task_type: str = Field(default='az_cli', description="The type of task: az_cli, python, deep_research, bash")
    prompt: str = Field(default="", description="The prompt describing the task to be accomplished")
    #bash_commands: Optional[List[str]] = Field(default=[], description="The generated bash command(s) for this task. Empty if task is not bash step")
    # az_cli_commands: Optional[List[str]] = Field(default=[], description="The generated Azure CLI command(s) for this task. Empty if task is not Azure CLI step")
    # az_cli_execution_result: Optional[List[AzShellToolExecutionResult]] = Field(default=None, description="The execution result of the Azure CLI commands for this task")
    # bash_execution_result: Optional[List[AzShellToolExecutionResult]] = Field(default=None, description="The execution result of the bash commands for this task")
    # python_execution_result: Optional[CodeToolExecutionResult] = Field(default=None, description="The execution result of the python code for this task")
    # deep_research_result: Optional[DeepResearchToolExecutionResult] = Field(default=None, description="The result of the deep web research for this task")
    
    #tool_execution_result: Optional[Dict[Literal['az_cli', 'python', 'deep_research', 'bash'], AzShellToolExecutionResult | CodeToolExecutionResult | DeepResearchToolExecutionResult]] = Field(default={}, description="The result from the tool execution for this task")
    # az_cli_tool_result: AzCliToolResult = Field(default=AzCliToolResult(), description="Azure CLI commands from tool based on user prompt")
    # code_tool_result: CodeToolResult = Field(default=CodeToolResult(), description="python code snippet from tool based on user prompt")
    # bash_tool_result: BashToolResult = Field(default=BashToolResult(), description="bash commands from tool based on user prompt")
    # deep_research_tool_result: DeepResearchToolResult = Field(default=DeepResearchToolResult(), description="deep web research results from tool based on user query")
    # tool: Optional[Tool] = Field(default=Tool(), description="The tool to be called in this step")
    # az_cli_command: Optional[str] = Field(default="", description="The generated Azure CLI command(s) for this step. Empty if task is Python step")
    # python: Optional[str] = Field(default="", description="The generated Python code snippet for this step. Empty if task is Azure CLI step")
    

class AzCliTaskCommandParameterResult(BaseModel):
    command: str = Field(default="", description="The Azure CLI command executed")
    execution_result: Optional[AzShellToolExecutionResult] = Field(default=AzShellToolExecutionResult(), description="The execution result of the Azure CLI command")
    missing_parameters: Optional[List[MissingParameters]] = Field(default=[], description="List of missing parameters for this command")

class AzCliTask(Task):
    commands: List[AzCliTaskCommandParameterResult] = Field(default=[], description="The generated Azure CLI command(s) for this task")

class PythonTask(Task):
    python_code: str = Field(default="", description="The generated Python code snippet for this task")
    execution_result: Optional[CodeToolExecutionResult] = Field(default=CodeToolExecutionResult(), description="The execution result of the python code for this task")
    missing_parameters: Optional[List[MissingParameters]] = Field(default=[], description="A dictionary describing what info is needed for each missing parameter")

class BashTaskCommandParameterResult(BaseModel):
    command: str = Field(default="", description="The Azure CLI command executed")
    execution_result: Optional[AzShellToolExecutionResult] = Field(default=AzShellToolExecutionResult(), description="The execution result of the Azure CLI command")
    missing_parameters: Optional[List[MissingParameters]] = Field(default=[], description="List of missing parameters for this command")

class BashTask(Task):
    commands: List[BashTaskCommandParameterResult] = Field(default=[], description="The generated bash command(s) for this task")


class DeepResearchTask(Task):
    query: str = Field(default="", description="The user query for deep web research")
    deep_research_result: Optional[DeepResearchToolExecutionResult] = Field(default=DeepResearchToolExecutionResult(), description="The result of the deep web research for this task")


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


# class ExecutionConfig(BaseModel):
#     username: str = Field(default="", description="The username of the person initiating the agent")
#     thread_id: str = Field(default="", description="The LangGraph thread id associated with this execution")
#     agent_cwd: str = Field(default="", description="The current working directory for the agent")


class Scratchpad(BaseModel):
    """
   scratchpad used by multi-agents to record notes and observations
    """
    original_prompt: str = Field(default="", description="The prompt describing the task to be accomplished")
    optimized_prompt: str = Field(default="", description="The optimized prompt after processing the original prompt")
    resolved_prompt: str = Field(default="", description="The resolved prompt with resolved Azure resource values")
    #missing_azure_values_in_prompt: MissingAzureValuesInPrompt = Field(default=MissingAzureValuesInPrompt(), description="A dictionary containing the missing information filled in by the user")
    #notes: dict = Field(default={}, description="A dict to hold general info or observations during workflow execution")
    task_plan: TaskPlan = Field(default=TaskPlan(), description="The execution plan containing all tasks")


from config import Config
class ExecutionState(BaseModel):
    username: str = Field(default="", description="The username of the person initiating the agent")
    tread_id: str = Field(default="", description="The LangGraph thread id associated with this execution")
    agent_working_directory: str = Field(default="", description="The current working directory for the agent")
    scratchpad: Scratchpad = Field(default=Scratchpad(), description="The scratchpad for temporary notes and observations")
    messages: Annotated[list[BaseMessage], Field(default=[], description="Conversation history"), add_messages]