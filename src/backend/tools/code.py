from smolagents import OpenAIServerModel, DuckDuckGoSearchTool, CodeAgent
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
load_dotenv()

class CodeToolInput(BaseModel):
    prompt: str = Field(..., description="The prompt to generate code for") 


class CodeTool(BaseTool):
    """Tool for generating code snippets using an OpenAI model."""

    def __init__ (self, model: OpenAIServerModel):
        deployment_name = os.getenv("OPENA_AI_MODEL_DEPLOYMENT_NAME")
        api_url = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")

        llm = OpenAIServerModel(
            model_id=deployment_name,
            api_base=api_url,
            api_key=api_key
        )

        self.code_agent = CodeAgent(model=llm, tools=[DuckDuckGoSearchTool()])

    name = "code_generator"
    description = "Generates code snippets based on a given prompt."

    def __init__(self, model: OpenAIServerModel):
        self.model = model

    def _run(self, prompt: str) -> str:
        """Generate code snippet from the given prompt."""
        raise NotImplementedError("Synchronous code generation is not implemented.")

    async def _arun(self, prompt: str) -> str:
        """Asynchronous version of the code generation."""
        response = await self.model.agenerate(prompt)
        return response.text