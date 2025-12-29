
from smolagents import OpenAIServerModel, DuckDuckGoSearchTool, CodeAgent, ToolCall, ActionStep, ActionOutput
from smolagents.agents import ActionStep, ActionOutput
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any, List, Optional, Dict
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, parent_dir)
from config import Config

# Get the absolute path of the parent directory
# parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.insert(0, parent_dir)
# from config import Config

# config = Config()

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
    # observations_images: list[PIL.Image.Image] | None = Field(default=None, description="Any images generated during the code action execution.")
    error: Optional[str] = Field(default=None, description="Error message if the code generation or execution failed.")
    llm_output: str = Field(default='', description="The output from the model after executing the code action.")
    tool_calls: List[CodeAgentToolCall] = Field(default=[], description="All tool calls made during code generation and execution.")

class CodeAgentActionOutput(BaseModel):
    """final output from the agent after executing all steps."""
    result: Any = Field(default=None, description="The final output from the code execution.")
    is_successful: bool = Field(default=False, description="Indicates whether this is the final answer from the agent.")

class CodeToolResult(BaseModel):
    # is_successful: bool = Field(default=False, description="Indicates whether the code generation and execution was successful.")
    # result: Any = Field(default=None, description="The final execution result.")
    # error: Optional[str] = Field(default='', description="Error message if the code generation or execution failed.")
    messages: Optional[List] = Field(default=[], description="The messages exchanged during the code generation and execution process.")
    action_steps: Optional[List[CodeAgentActionStep]] = Field(default=[], description="All action steps taken during code generation and execution.")
    action_outputs: Optional[List[CodeAgentActionOutput]] = Field(default=[], description="The final output from the agent after executing all steps.")
    tool_calls: Optional[List[CodeAgentToolCall]] = Field(default=[], description="All tool calls made during code generation and execution.")

    def final_result(self) -> CodeAgentActionOutput:
        result = self.action_outputs[-1] if self.action_outputs else None
        return result

# class CodeToolOutput(BaseModel):
#     output: CodeToolResult = Field(default=None, description="The final output from the code execution.")
#     messages: List = Field(default=[], description="The messages exchanged during the code generation and execution process.")
#     tool_calls: List = Field(default=[], description="all tool calls made during code generation and execution.")


class CodeTool(BaseTool):
    """
    This tool is a wrapper around SmolAgents CodeAgent to generate and execute code snippets based on a given prompt.
    """

    name: str = "python_code_executor"
    description: str = """
    1. Generate Python code to solve tasks. Python code is the primary action mechanism - use this tool to directly solve problems by writing and executing code.
    2. Option to execute the generated Python code to obtain results.
    3. Save the generated code to a local file if specified.

    Capabilities:
    - Write and run Python code for any computational task
    - Read and write files on the local file system
    - Use pandas, numpy, matplotlib, seaborn for data analysis and visualization
    - Perform calculations, data transformations, file operations, and automation
    - Generate charts, reports, and save outputs to disk
    - more...

    Use this tool when you need to:
    - Processing or analyzing data files (CSV, JSON, etc.)
    - Create visualizations or charts
    - Perform mathematical calculations or data transformations
    - Read/write/manipulate files
    - Execute any task that requires Python code
    """

    args_schema: Type[BaseModel] = CodeToolInput
    response_format: Type[BaseModel] = CodeToolResult


    def _run(self, prompt: str) -> str:
        """Generate code snippet from the given prompt."""
        raise NotImplementedError("Synchronous code generation is not implemented.")


    async def _arun(self, prompt: str, agent_cwd: str = None, execute_code: Optional[bool] = True, **kwargs) -> CodeToolResult:
        """Asynchronous version of the code generator and executor"""

        try:

            config = Config()

            deployment_name = config.azure_openai_deployment_name
            foundry_endpoint = config.foundry_endpoint
            api_key = config.azure_openai_api_key

            llm = OpenAIServerModel(
                model_id=deployment_name,
                api_base=foundry_endpoint,
                api_key=api_key
            )
            
            authorized_imports = [
                "os", "sys", "json", "csv", "math", "random", "datetime", "time", 
                "re", "itertools", "functools", "collections", "pathlib", "io",
                "base64", "hashlib", "uuid", "copy", "pickle", "statistics", "string",
                "textwrap", "difflib", "yaml", "configparser", "gzip", 
                "zipfile", "tarfile", "logging", "warnings", "array", "typing",
                "dataclasses", "enum", "decimal", "stat", "queue", "seaborn", 
                "numpy", "pandas", "unicodedata", "matplotlib", 'matplotlib.pyplot', 'matplotlib.figure', 
                'matplotlib.axes', 'matplotlib.patches', 'matplotlib.lines', 'matplotlib.markers', 'matplotlib.path',
                'matplotlib.transforms',
                'matplotlib.animation',
                'matplotlib.artist',
                'matplotlib.collections',
                'matplotlib.colorbar',
                'matplotlib.colors',
                'matplotlib.cm',
                'matplotlib.contour',
                'matplotlib.font_manager',
                'matplotlib.text',
                'matplotlib.image',
                'matplotlib.dates',
                'matplotlib.ticker',
                'matplotlib.gridspec',
                'matplotlib.style',
                'matplotlib.widgets',
                'matplotlib.legend',
                'matplotlib.scale',
                'matplotlib.table'
            ] #'bs4'

            prompt_template = """

            - You have full access to local file system within the working directory: {agent_cwd}. Anything you do with files must be done within this directory.
            - Whenever user request to analyze files or process data from any Azure service or request to download any files, make sure to read/write files only within this directory: {agent_cwd}.
            - The Python code you generate can read and write files in this directory '{agent_cwd}' as needed to complete the task.
            
            <user request>
            {prompt}

            <output>
            You must provide the final output in <JSON format> as below.
            
            * Only at final thought and observation with no alternate solution and if error occurs , provide help technical error message to support debugging.
            * If is not final thought and observation and has alternate solution to try, do not provide error message.

            <JSON format>
            {{
                'is_successful': {{true or false}},
                "result": {{the final execution result in string}}
            }}
            """


            prompt = prompt_template.format(
                agent_cwd=agent_cwd,
                prompt=prompt
            )

            code_agent = CodeAgent(model=llm, 
                                   use_structured_outputs_internally=True,
                                   additional_authorized_imports=authorized_imports,
                                   executor_type="local",
                                   tools=[DuckDuckGoSearchTool()])

            result = CodeToolResult()


            stream_generator = code_agent.run(prompt, stream=True)

            for response in stream_generator:
                
                if self._has_messages(response):
                    result.messages = response.model_input_messages

                if self._is_tool_call(response):
                    result.tool_calls.append(CodeAgentToolCall(
                        name=response.name,
                        arg=response.arguments
                    ))

                if self._is_action_step(response):
                    action_step = CodeAgentActionStep(
                        step_number=response.step_number or -1,
                        code_action=response.code_action or None,
                        action_output=response.action_output or None,
                        observations=response.observations or None,
                        error=str(response.error) or None,
                        llm_output=response.model_output or None,
                        tool_calls=[
                            CodeAgentToolCall(
                                name=tool_call.name,
                                arg=tool_call.arguments
                            ) for tool_call in response.tool_calls
                        ]
                    )
                    result.action_steps.append(action_step)
               
                if self._is_action_output(response):
                    if response.output and 'result' in response.output:
                        result.action_outputs.append(CodeAgentActionOutput(
                            is_successful = response.output['is_successful'],
                            result = response.output['result']
                        ))
                
                # if self._has_output(response):
                #     result.output = response.output

                # if self._error(response) and self._is_final_answer(response):
                #     result.error = response.error

            return result
        
        except Exception as e:
            result = CodeToolResult()
            result.action_outputs = [CodeAgentActionOutput(
                is_successful=False,
                result=str(e)
            )]
            return result

        
    def _is_tool_call(self, obj: any) -> bool:
        return isinstance(obj, ToolCall)
    
    def _is_action_step(self, obj: any) -> bool:
        return isinstance(obj, ActionStep)
    
    def _is_action_output(self, obj: any) -> bool:
        """represents the final output from the agent after executing all steps."""
        return isinstance(obj, ActionOutput)
    
    def _has_messages(self, obj: any) -> bool:
        return hasattr(obj, 'model_input_messages')
    
    def _is_final_answer(self, obj: any) -> bool:
        return hasattr(obj, 'is_final_answer ') and obj.is_final_answer == True
    
    # def _error(self, obj: any) -> bool:
    #     return hasattr(obj, 'error')
    
    # def _has_output(self, obj: any) -> bool:
    #     return hasattr(obj, 'output')


# test tool
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    username = 'admin@MngEnvMCAP049172.onmicrosoft.com'
    agent_cwd = os.path.join(os.getenv("AGENT_WORKING_DIRECTORY"), username)

    code_tool = CodeTool()
    prompt_1 = "Write a Python function to calculate the factorial of number 5, run it and print result."

    read_file_prompt_1 = f"""
     Accessa and analyze seattle_temperature.csv file process the data, 
     give me a summary of what this data is about.
    """
    
    result: CodeToolResult = asyncio.run(code_tool._arun(prompt=read_file_prompt_1, agent_cwd=agent_cwd, execute_code=False))

    result = result.final_result()

    print(result)