from contextlib import asynccontextmanager
import json
from typing import AsyncGenerator, Any
from langchain.tools import BaseTool
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field


class AzCliToolResult(BaseModel):
    prompt: str = Field(default='', description="'The user intent of the task to be solved by using the CLI tool.'")
    success: bool = Field(default=False, description="'Indicates whether the Azure CLI command was generated successfully.'")
    commands: list[str] = Field(default=[], description="'The list of generated Azure CLI command(s).'")
    error: str = Field(default='', description="'Error message if the command generation failed.'")

class AzureMcpTools:

    def __init__(self):
        self.az_cli_tool_name = "extension_cli_generate"
        self.server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@azure/mcp@latest", "server", "start"],
                env=None
        )

    async def az_cli_tool(self) -> AsyncGenerator[BaseTool, None]:
        """
        Context manager that provides the Azure CLI command generation tool.
        
        Usage:
            async with az_cli_tool() as tool:
                result = await tool.ainvoke({"intent": "list all VMs"})
        
        returns:
            BaseTool: The Azure CLI command generation tool
        """
        
        async with self.az_mcp_session() as session:

            # Load the MCP tools into a list of LangChain BaseTool objects
            langchain_tools: list[BaseTool] = await load_mcp_tools(session)

            # Format tools for Azure OpenAI
            tools = [tool for tool in langchain_tools if tool.name == self.az_cli_tool_name]

            assert tools, "Error at Azure MCP tools, no Azure CLI generation tool found."
            assert len(tools) == 1, "Error at Azure MCP tools, expected exactly one Azure CLI generation tool."

            return tools[0]
        
    
    async def ainvoke_az_cli_tool(self, prompt: str) -> AsyncGenerator[BaseTool, None]:
        """
        Context manager that provides the Azure CLI command generation tool.
        
        Usage:
            async with az_cli_tool() as tool:
                result = await tool.ainvoke({"intent": "list all VMs"})
        
        Yields:
            BaseTool: The Azure CLI command generation tool
        """
        
        async with self.az_mcp_session() as session:

            # Load the MCP tools into a list of LangChain BaseTool objects
            langchain_tools: list[BaseTool] = await load_mcp_tools(session)

            # Format tools for Azure OpenAI
            tools = [tool for tool in langchain_tools if tool.name == self.az_cli_tool_name]

            assert tools, "Error at Azure MCP tools, no Azure CLI generation tool found."
            assert len(tools) == 1, "Error at Azure MCP tools, expected exactly one Azure CLI generation tool."

            azcli = tools[0]

            mcp_result = await azcli.ainvoke(input={
                    "intent": prompt,
                    "cli-type": "az"
                })

            result = AzCliToolResult(prompt=prompt)
            
            for r in mcp_result:
                td = json.loads(r['text'])
                result.success = True if td.get('message', '').lower() == 'success' else False
                command_data = td.get('results', '').get('command', '{}')
                command_data = json.loads(command_data)

                for cd in command_data.get('data', []):
                    for cs in cd.get('commandSet', []):
                        result.commands.append(cs.get('example', ''))

            return result

        
        
    @asynccontextmanager
    async def az_mcp_session(self) -> AsyncGenerator[ClientSession, None]:
        """
        Context manager that provides an MCP ClientSession.
        
        Usage:
            async with az_mcp_session() as session:
                # Use the session here
        
        Yields:
            ClientSession: The MCP ClientSession
        """
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


# @asynccontextmanager
# async def az_doc_tool() -> AsyncGenerator[BaseTool, None]:
#     """
#     Context manager that provides the Azure documentation
    
#     Usage:
#         async with azcli_command_tool() as tool:
#             result = await tool.ainvoke({"intent": "list all VMs"})
    
#     Yields:
#         BaseTool: The Azure CLI command generation tool
#     """
    
#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()

#             # Load the MCP tools into a list of LangChain BaseTool objects
#             langchain_tools: list[BaseTool] = await load_mcp_tools(session)

#             # Format tools for Azure OpenAI
#             tools = [tool for tool in langchain_tools if tool.name == "documentation"]

#             assert tools, "Error at Azure MCP tools, no Azure documentation tool found."
#             assert len(tools) == 1, "Error at Azure MCP tools, expected exactly one Azure documentation tool."

#             yield tools[0]


# class AzureMcpTools:

#     @staticmethod
#     async def get_tools() -> dict[str, BaseTool]:
#         """
#         Get the Azure MCP tools as a dictionary of context managers.

#         Returns:
#             dict[str, Any]: A dictionary with tool names as keys and context managers as values.
#         """

#         async with stdio_client(server_params) as (read, write):
#             async with ClientSession(read, write) as session:
#                 await session.initialize()

#                 # Load the MCP tools into a list of LangChain BaseTool objects
#                 langchain_tools: list[BaseTool] = await load_mcp_tools(session)

#                 # Format tools for Azure OpenAI
#                 tools = [tool for tool in langchain_tools if tool.name in tool_in_use]

#                 assert tools, "Error at Azure MCP tools, no Azure documentation tool found."
#                 assert len(tools) == 3, "Error at Azure MCP tools, expected exactly one Azure documentation tool."

#         return {k: v for tool in tools for k, v in {tool.name: tool}.items()}


            