from smolagents import OpenAIServerModel, DuckDuckGoSearchTool, CodeAgent
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import os
from dotenv import load_dotenv
load_dotenv()

class CodeToolInput(BaseModel):
    prompt: str = Field(..., description="The prompt to generate code for") 


class CodeToolResult(BaseModel):
    success: bool = Field(default=False, description="Indicates whether the code generation and execution was successful.")
    result: str = Field(default='', description="The output from executing the generated code.")
    error: str = Field(default='', description="Error message if the code generation or execution failed.")


class CodeTool(BaseTool):
    """
    This tool is a wrapper around SmolAgents CodeAgent to generate and execute code snippets based on a given prompt.
    """

    name: str = "code_generator_executor"
    description:str = """
    Generates and executes Python code. Returns execution output.

    Important: 
    - This tool ONLY generates and runs code
    - To save files → use write_file_tool
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

        deployment_name = os.getenv("OPENA_AI_MODEL_DEPLOYMENT_NAME")
        api_url = os.getenv("FOUNDRY_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")

        llm = OpenAIServerModel(
            model_id=deployment_name,
            api_base=api_url,
            api_key=api_key
        )

        code_agent = CodeAgent(model=llm, tools=[DuckDuckGoSearchTool()])

        stream_generator = code_agent.run(prompt, stream=True)
        for response in stream_generator:
            print(response)  # Iterate to the end to get the final response

        return response.output
    

# test tool
if __name__ == "__main__":
    import asyncio

    code_tool = CodeTool()
    prompt = "Write a Python function to calculate the factorial of number 5, run it and print result."
    
    result = asyncio.run(code_tool._arun(prompt))
    print(result)