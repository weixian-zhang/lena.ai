from langchain_openai import AzureChatOpenAI
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, List, Type
from agents.utils import Util

class BashToolInput(BaseModel):
    prompt: str = Field(description="the prompt to generate bash command for")

class BashToolOutput(BaseModel):
    commands: List[str] = Field(description="The generated bash command based on the prompt.")

class BashToolResult(BaseModel):
    is_success: bool = Field(description="Indicates whether the bash command was generated successfully.")
    commands: Optional[List[str]] = Field(description="The generated bash command based on the prompt.")
    error: Optional[str] = Field(default=None, description="The result of executing the generated bash command, if applicable.")


class BashTool(BaseTool):
    name: str = "bash_command_generator"
    description: str = """
    generates bash commands based on user prompt.
    Use this tool to directly to any generate Linux Bash commands like: Docker build and run commands, text processing with 'cat', 'grep', 'head', 'tail', file and directory operations with 'touch', 'mkdir', 'ls', 'cd', 'mv', 'cp', 'rm' and etc.
    """
    args_schema: Type[BaseModel] = BashToolInput
    response_format: Type[BaseModel] = BashToolResult

    def _run(self, prompt: str) -> BashToolResult:
        """Generate code snippet from the given prompt."""
        raise NotImplementedError("Synchronous code generation is not implemented.")


    async def _arun(self, prompt: str) -> BashToolResult:
        """Asynchronously generate bash command from the given prompt.""" 
        
        try:

            llm : AzureChatOpenAI = Util.gpt_4o()
            llm = llm.with_structured_output(BashToolOutput)
            
            messages = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(content="""
                    You are a Linux bash command generator.
                                
                    <Key Requirements>
                    1. Generate one or a list of multiple bash commands to fulfill the user prompt task.
                    2. Always generate only the bash commands without any explanation.
                                
                    <command generation scenarios>
                    - Docker build and run commands like docker build, docker runtext processing with 'cat', 'grep', 'head', 'tail', file and directory operations with 'touch', 'mkdir', 'ls', 'cd', 'mv', 'cp', 'rm' and etc.
                    - text processing with 'cat', 'grep', 'head', 'tail'
                    - file and directory operations with 'touch', 'mkdir', 'ls', 'cd', 'mv', 'cp', 'rm'
                    - more...
                    
                    <Examples>
                    1. User prompt: "Create a new directory named 'test_dir' and navigate into it."
                    Generated bash command: {
                                  commands: ["mkdir test_dir", "cd test_dir"]
                    }
                    2. User prompt: "List all files in the current directory with detailed information."
                    Generated bash command: {
                                  commands: ["ls -l"]
                    }
                    3. User prompt: "Display the first 10 lines of a file named 'example.txt'."
                    Generated bash command: {
                                  commands: ["head -n 10 example.txt"]
                    }
                    """),
                    HumanMessage(content=prompt)
                ]   
            )

            chain = messages | llm

            output: BashToolOutput = chain.invoke({})

            bash_commands = output.commands

            return BashToolResult(
                is_success=True,
                commands=bash_commands,
                error="")

        except Exception as e:
            return BashToolResult(
                is_success=False,
                bash_command="",
                error=str(e))
        

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    bash_tool = BashTool()
    prompt = """authenticate to docker hub with username 'myuser' and password 'mypassword', 
    then pull the latest nginx image and 
    run a container named 'mynginx' mapping host port 8080 to container port 80."""

    result: BashToolResult = asyncio.run(bash_tool._arun(prompt))

    print(result)
