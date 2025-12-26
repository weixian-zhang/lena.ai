from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class CodeGeneratorToolInput(BaseModel):
    prompt: str = Field(..., description="The prompt to generate code for")

class CodeGeneratorToolResult(BaseModel):
    python_code: str = Field(default='', description="The generated Python code snippet that accomplishes the task described in the prompt.")
    success: bool = Field(default=False, description="Indicates whether the code generation was successful.")
    error: str = Field(default='', description="Error message if the code generation failed.")


class CodeGeneratorTool(BaseTool):
    """
    This tool is a wrapper around SmolAgents CodeAgent to generate code snippets based on a given prompt.
    """

    name: str = "python_code_generator"
    description: str = """
    Generates Python code to solve tasks. This is your primary tool for taking action through code.

    Capabilities:
    - Write and run Python code for any computational task
    - Read and write files on the local file system
    - Use pandas, numpy, matplotlib, seaborn for data analysis and visualization
    - Perform calculations, data transformations, file operations, and automation
    - Generate charts, reports, and save outputs to disk
    - more...

    Input:
    - A prompt describing the task to be accomplished

    Output:
    - A Python code snippet that accomplishes the task described in the prompt
    """