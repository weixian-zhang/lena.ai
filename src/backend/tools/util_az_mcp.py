from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from langchain.tools import BaseTool
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@azure/mcp@latest", "server", "start"],
        env=None
)

@asynccontextmanager
async def az_cli_command_tool() -> AsyncGenerator[BaseTool, None]:
    """
    Context manager that provides the Azure CLI command generation tool.
    
    Usage:
        async with az_cli_command_tool() as tool:
            result = await tool.ainvoke({"intent": "list all VMs"})
    
    Yields:
        BaseTool: The Azure CLI command generation tool
    """
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Load the MCP tools into a list of LangChain BaseTool objects
            langchain_tools: list[BaseTool] = await load_mcp_tools(session)

            # Format tools for Azure OpenAI
            tools = [tool for tool in langchain_tools if tool.name == "extension_cli_generate"]

            assert tools, "Error at Azure MCP tools, no Azure CLI generation tool found."
            assert len(tools) == 1, "Error at Azure MCP tools, expected exactly one Azure CLI generation tool."

            yield tools[0]


@asynccontextmanager
async def az_doc_tool() -> AsyncGenerator[BaseTool, None]:
    """
    Context manager that provides the Azure documentation
    
    Usage:
        async with azcli_command_tool() as tool:
            result = await tool.ainvoke({"intent": "list all VMs"})
    
    Yields:
        BaseTool: The Azure CLI command generation tool
    """
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Load the MCP tools into a list of LangChain BaseTool objects
            langchain_tools: list[BaseTool] = await load_mcp_tools(session)

            # Format tools for Azure OpenAI
            tools = [tool for tool in langchain_tools if tool.name == "documentation"]

            assert tools, "Error at Azure MCP tools, no Azure documentation tool found."
            assert len(tools) == 1, "Error at Azure MCP tools, expected exactly one Azure documentation tool."

            yield tools[0]

            