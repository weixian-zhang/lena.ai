from tools.az_cli import AzCliTool, AzCliToolResult
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any

# class ToolPack(BaseModel):
#     is_azure_mcp_tool: bool = Field(default=False, description="'Indicates whether the tool is an Azure MCP tool.'")
#     tool: BaseTool = Field(default=None, description="'LangChain StructuredTool instance.'")

# class ToolResult(BaseModel):
#     success: bool = Field(default=False, description="'Indicates whether the tool invocation was successful.'")
#     data: Any = Field(default='', description="'The data from the tool invocation.'")
#     error: str = Field(default='', description="'Error message if the tool invocation failed.'")


class ToolManager:

    def __init__(self):
        self.az_cli_tool = AzCliTool()
    
    
    async def azcli_tool(self):
        azcli_tool = await self.az_cli_tool.get()
        return azcli_tool

    
    async def ainvoke_azcli_tool(self, prompt: str) -> AzCliToolResult:
        result: AzCliToolResult = await self.az_cli_tool.ainvoke(prompt)
        return result

