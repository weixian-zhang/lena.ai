from langchain_core.tools import BaseTool
from abc import abstractmethod

class AgentTool(BaseTool):
    name: str
    description: str

    def _run(self, tool_input: str) -> str:
        raise NotImplementedError("This method will not be implemented.")
    
    @abstractmethod
    async def _arun(self, tool_input: str) -> str:
        raise NotImplementedError("This method should be overridden by subclasses.")