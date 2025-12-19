from smolagents import OpenAIServerModel, DuckDuckGoSearchTool, CodeAgent, ToolCall
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any, List
import os, sys
from file_system.smol_read_file import SmolReadFileTool
from dotenv import load_dotenv
load_dotenv()

# Get the absolute path of the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
from config import Config

config = Config()

class CodeToolInput(BaseModel):
    prompt: str = Field(..., description="The prompt to generate code for") 

class CodeAgentToolCall(BaseModel):
    name: str = Field(..., description="name of tool")
    arg: str = Field(..., description="generated code snippet to execute")

class CodeToolResult(BaseModel):
    success: bool = Field(default=False, description="Indicates whether the code generation and execution was successful.")
    output: Any = Field(default=None, description="The final output from the code execution.")
    messages: List = Field(default=[], description="The messages exchanged during the code generation and execution process.")
    tool_calls: List = Field(default=[], description="all tool calls made during code generation and execution.")
    error: str = Field(default='', description="Error message if the code generation or execution failed.")

code_agent_prompt_templates = {
    # "system_prompt": """
    # You are a highly skilled Python programmer and code executor.
    # Your task is to generate Python code snippets based on user prompts and execute them to obtain results.
    # You have access to a set of <tools> to assist you in this process.
    
    # <tools>
    # 1. DuckDuckGoSearchTool: Use this tool to search the web for information that can help you generate accurate and effective code snippets.
    # 2. read_file_tool: Use this tool to read text content, code, or data from a file.
    
    # """,

    "final_answer": """
    use the following format for final answer:
    {
        "output": <final output from code execution>
    }
    """
}
class CodeTool(BaseTool):
    """
    This tool is a wrapper around SmolAgents CodeAgent to generate and execute code snippets based on a given prompt.
    """

    name: str = "code_generator_executor"
    description:str = """
    read the data CSV file from local file system, process the data, and generate insights or visualizations as needed.

    Important: 
    - This tool ONLY generates and runs code
    - To read files → use read_file_tool  
    - To list directories → use list_files_tool

    Use for data processing, calculations, transformations, and automation tasks.
    """

    args_schema: Type[BaseModel] = CodeToolInput
    response_format: Type[BaseModel] = CodeToolResult


    def _run(self, prompt: str) -> str:
        """Generate code snippet from the given prompt."""
        raise NotImplementedError("Synchronous code generation is not implemented.")


    async def _arun(self, prompt: str) -> str:
        """Asynchronous version of the code generator and executor"""

        try:

            deployment_name = os.getenv("OPENA_AI_MODEL_DEPLOYMENT_NAME")
            api_url = os.getenv("FOUNDRY_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")

            llm = OpenAIServerModel(
                model_id=deployment_name,
                api_base=api_url,
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

            code_agent = CodeAgent(model=llm, 
                                   use_structured_outputs_internally=True,
                                   additional_authorized_imports=authorized_imports,
                                   executor_type="local",
                                   tools=[DuckDuckGoSearchTool()])

            tool_calls = []
            messages = []
            output: Any = None

            stream_generator = code_agent.run(prompt, stream=True)
            for response in stream_generator:
                
                if self._has_messages(response):
                    messages = response.model_input_messages

                if self._is_tool_call(response):
                    tool_calls.append(CodeAgentToolCall(
                        name=response.name,
                        arg=response.arguments
                    ))
                
                if self._has_output(response):
                    output = response.output

                print(response)  # Iterate to the end to get the final response

            return CodeToolResult(
                success=True,
                output=output,
                messages=messages,
                tool_calls=tool_calls,
                error='')
        
        except Exception as e:
            return CodeToolResult(
                success=False,
                output=None,
                error=str(e))
        
    def _is_tool_call(self, obj: any) -> bool:
        return isinstance(obj, ToolCall)
    
    def _has_messages(self, obj: any) -> bool:
        return hasattr(obj, 'model_input_messages')
    
    def _has_output(self, obj: any) -> bool:
        return hasattr(obj, 'output')


# test tool
if __name__ == "__main__":
    import asyncio

    code_tool = CodeTool()
    prompt_1 = "Write a Python function to calculate the factorial of number 5, run it and print result."

    read_file_prompt_1 = f"""
     Accessa and analyze the data CSV file from local file system in this directory {config.agent_cwd}, process the data, 
     and generate bar chart visualization of temperature over time.
     Bar chart image can be save to local file system in this directory {config.agent_cwd} as 'temperature_chart.png'.
    """
    
    result = asyncio.run(code_tool._arun(read_file_prompt_1))
    print(result)