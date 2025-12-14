from langchain_core.tools import tool, Tool, BaseTool
from mcp import ClientSession, StdioServerParameters, types
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field
from typing import Type
from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from dotenv import load_dotenv
load_dotenv()

class AzCliToolSchema(BaseModel):
    prompt: str = Field(description="'The user intent of the task to be solved by using the CLI tool. This user intent will be used to generate the appropriate CLI command to accomplish the desirable goal.'")

class AzCliToolResult(BaseModel):
    success: bool = Field(default=False, description="'Indicates whether the Azure CLI command was generated successfully.'")
    az_commands: list[str] = Field(default=[], description="'The generated Azure CLI command as a string.'")

class AzCliTool(BaseTool):
    """
    A class to generate Azure CLI commands for managing resources.
    """
    name: str = "extension_cli_generate"
    description: str = "'This tool can generate Azure CLI commands to be used with the corresponding CLI tool to accomplish a goal described by the user. This tool incorporates knowledge of the CLI tool beyond what the LLM knows. Always use this tool to generate the CLI command when the user asks for such CLI commands or wants to use the CLI tool to accomplish something.'"
    args_schema: Type[BaseModel] = AzCliToolSchema
    azcli_tool: Tool = Field(default=None, description="The Azure CLI tool loaded from MCP session.")
    

    def _run(self, prompt: str) -> AzCliToolResult:
        """The synchronous method that the agent will call."""
        # This is where your custom logic or API call goes
        raise NotImplementedError("Synchronous execution is not implemented. Please use the asynchronous method '_arun'.")

    async def _arun(self, prompt: str) -> AzCliToolResult:
        """The asynchronous method for the tool (optional)."""

        try:
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@azure/mcp@latest", "server", "start"],
                env=None
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # Load the MCP tools into a list of LangChain BaseTool objects
                    langchain_tools: list[BaseTool] = await load_mcp_tools(session)

                    # List available tools
                    # tools = await session.list_tools()
                    # for tool in tools.tools: print(tool.name)

                    # Format tools for Azure OpenAI
                    tools = [tool for tool in langchain_tools if tool.name == "extension_cli_generate"]

                    result = await tools[0].ainvoke(input={
                        "intent": prompt,
                        "cli-type": "az"
                    })

                    azcli_result = AzCliToolResult()

                    for r in result:
                        td = json.loads(r['text'])
                        azcli_result.success = True if td.get('message', '').lower() == 'success' else False
                        command_data = td.get('results', '').get('command', '{}')
                        command_data = json.loads(command_data)

                        for cd in command_data.get('data', []):
                            for cs in cd.get('commandSet', []):
                                azcli_result.az_commands.append(cs.get('example', ''))

                    return azcli_result
        except Exception as e:
            raise Exception(f"Error generating Azure CLI command: {e}") from e
        

    def _add_event_internal(self, summary, start, end):
        # Your internal business logic
        return f"Internal success for {summary}"
    
    async def _add_event_internal_async(self, summary, start, end):
        # Your internal async business logic
        return f"Async internal success for {summary}"
    

if __name__ == "__main__":
    import asyncio

    async def main():
        azcli_tool_instance = AzCliTool()
        result = await azcli_tool_instance.ainvoke(
            {'prompt': """
            create a virtual network named 'myVNet' in resource group 'myResourceGroup' with address prefix 172.15.0.0/16 and a subnet named 'mySubnet' with address prefix 172.15.1.0/24.
            Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size and in virtual network myVNet.
             """}
        )
        print(result)

    asyncio.run(main())


    # async def _load_azure_mcp_azcli_tool(self) -> Tool:
    #     server_params = StdioServerParameters(
    #         command="npx",
    #         args=["-y", "@azure/mcp@latest", "server", "start"],
    #         env=None
    #     )

    #     async with stdio_client(server_params) as (read, write):
    #         async with ClientSession(read, write) as session:
    #             await session.initialize()

    #             # Load the MCP tools into a list of LangChain BaseTool objects
    #             langchain_tools: list[BaseTool] = await load_mcp_tools(session)

    #             langchain_tools = [tool for tool in langchain_tools if tool.name == "extension_cli_generate"]

    #             result = await langchain_tools[0].ainvoke(input={
    #                 "intent": """
    #                 create a virtual network named 'myVNet' in resource group 'myResourceGroup' with address prefix 172.15.0.0/16 and a subnet named 'mySubnet' with address prefix 172.15.1.0/24.
    #                 Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size and in virtual network myVNet.
    #                 """,
    #                 "cli-type": "az"
    #             })

    #             az_cmds = []

    #             for r in result:

    #                 az_cmds.append(json.loads(r['text']))

    #             pass


        # mcp_config = {
        #     "azure_mcp": {
        #         "command": "npx",
        #         "args": [
        #             "-y", # Automatically install the package if not found
        #             "@azure/mcp@latest"
        #             # Add any other required arguments for your specific server
        #         ],
        #         "transport": "stdio" # Use standard input/output for local process communication
        #     }
        # }

        # 2. Initialize the MultiServerMCPClient
        # The client manages the server lifecycle (starts it as a subprocess)
        # client = MultiServerMCPClient(connections=mcp_config)

        # async with client.session("azure_mcp") as session:

        #     langchain_tools: list[BaseTool] = await load_mcp_tools(session)

        #     assert langchain_tools is not None, "No tools found from MCP session."

        #     tools = [tool for tool in tools if tool.name == "extension_cli_generate"]
            
        #     assert len(tools) == 1, "Expected exactly one Azure CLI generation tool."

        #     return tools[0]

    # @tool
    # def generate_execute_azure_cli_command(self, prompt: str) -> dict:
    #     """
    #     This tool can generate Azure CLI commands to be used with the corresponding CLI tool to accomplish a goal described by the user. This tool incorporates knowledge of the CLI tool beyond what the LLM knows. Always use this tool to generate the CLI command when the user asks for such CLI commands or wants to use the CLI tool to accomplish something.

    #     :param prompt: a prompt to describe Azure operation to be performed and its parameters preferably. The Azure CLI command will be genrated internally for example: az vm create --resource-group myResourceGroup --name myVM --image UbuntuLTS --size Standard_DS1_v2
    #     :return: dictionary of Azure CLI command execution result
    #     """

    #     cmd = self.azcli_tool.invoke({"intent": prompt})
    #     return {}
    



