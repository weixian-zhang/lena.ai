from contextlib import asynccontextmanager
import json
from typing import AsyncGenerator
from langchain.tools import BaseTool
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from typing import Type

import os, sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
from state import AzCliToolResult, AzureCliToolInput

class AzCliTool(BaseTool):
    name: str = "azure_cli_generate"
    description: str = """
    'This tool can generate Azure CLI commands to be used with the corresponding CLI tool to accomplish a goal described by the user.
    This tool incorporates knowledge of the CLI tool beyond what the LLM knows. Always use this tool to generate the CLI command when the user asks for such CLI commands or wants to use the CLI tool to accomplish something.'

    Capabilities:
    - Create, update, delete, and query Azure resources
    - Manage resource groups, subscriptions, and deployments
    - Configure Azure services (VMs, storage, networking, databases, etc.)
    - Retrieve resource information and status
    - Execute Azure administrative tasks

    Use this tool when you need to:
    - Perform any Azure cloud operation
    - Manage Azure resources programmatically
    - Query Azure resource information
    - Automate Azure infrastructure tasks
    """
    args_schema: Type[BaseModel] = AzureCliToolInput
    response_format: Type[BaseModel] = AzCliToolResult


    def _run(self, prompt: str) -> str:
        """Generate code snippet from the given prompt."""
        raise NotImplementedError("Synchronous code generation is not implemented.")


    async def _arun(self, prompt: str) -> str:
        """Asynchronously generate Azure CLI command from the given prompt."""

        az_cli_mcp_tool_name = "extension_cli_generate"

        async with self.az_mcp_session() as session:

            # Load the MCP tools into a list of LangChain BaseTool objects
            langchain_tools: list[BaseTool] = await load_mcp_tools(session)

            # Format tools for Azure OpenAI
            tools = [tool for tool in langchain_tools if tool.name == az_cli_mcp_tool_name]

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
        
        server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@azure/mcp@latest", "server", "start"],
                env=None
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session




if __name__ == "__main__":
    import asyncio
    from az_shell import AzShell

    async def main():
        az_cli_tool = AzCliTool()

        prompt_1 = "create a new Function app named <function_app_name> in resource group <resource_group_name> with Docker container using existing Storage account name 'strgcwhd' "
        prompt_2 = "create new VM name <vm_name_1> in virtual network <virtual_network_name_1> in subnet <subnet_name_1> in resource group 'rg-production-eastus' with VM size <vm_size> and vm image <vm_image>"

        result: AzCliToolResult = await az_cli_tool.ainvoke({
            "prompt": prompt_2
        })
        # azcli: 'az vm create --resource-group rg-production-eastus --name <vm_name_1> --vnet-name <virtual_network_name_1> --subnet <subnet_name_1> --image <vm_image> --size <vm_size> --generate-ssh-keys'
        result.commands[0]

        az_shell = AzShell()
        result = await az_shell.ainvoke(result.commands[0], timeout=1)
        print(result)

    asyncio.run(main())


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


            