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
    success: bool = Field(description="'Indicates whether the Azure CLI command was generated successfully.'")
    az_cli_commands: list[str] = Field(description="'The generated Azure CLI command as a string.'")

class AzCliTool(BaseTool):
    """
    A class to generate Azure CLI commands for managing resources.
    """
    name: str = "extension_cli_generate"
    description: str = "'This tool can generate Azure CLI commands to be used with the corresponding CLI tool to accomplish a goal described by the user. This tool incorporates knowledge of the CLI tool beyond what the LLM knows. Always use this tool to generate the CLI command when the user asks for such CLI commands or wants to use the CLI tool to accomplish something.'"
    args_schema: Type[BaseModel] = AzCliToolSchema
    azcli_tool: Tool = Field(default=None, description="The Azure CLI tool loaded from MCP session.")

    # def __init__(self):
    #     self.azcli_tool: Tool = None

    # @classmethod
    # async def create(cls):
    #     self = cls()
    #     azcli_tool = await self._load_azure_mcp_azcli_tool()
    #     self.azcli_tool = azcli_tool
    #     return self
    

    def _run(self, prompt: str) -> str:
        """The synchronous method that the agent will call."""
        # This is where your custom logic or API call goes
        azclicmd = self.azcli_tool.invoke({"intent": prompt})
        return azclicmd

    async def _arun(self, prompt: str) -> str:
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
                        "intent": "Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size.",
                        "cli-type": "az"
                    })

                    az_cmds = []

                    for r in result:
                        td = json.loads(r['text'])
                        success = True if td.get('message', '').lower() == 'success' else False
                        command_data = json.td.get('results', '').get('command', '{}')

                        for cd in command_data.get('data', []):
                            for cs in cd.get('commandSet', []):
                                az_cmds.append(cs.get('example', ''))

                    return az_cmds
        except Exception as e:
            raise Exception(f"Error generating Azure CLI command: {e}") from e
        

    def _add_event_internal(self, summary, start, end):
        # Your internal business logic
        return f"Internal success for {summary}"
    
    async def _add_event_internal_async(self, summary, start, end):
        # Your internal async business logic
        return f"Async internal success for {summary}"
    
    async def _load_azure_mcp_azcli_tool(self) -> Tool:
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
                    "intent": "Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size.",
                    "cli-type": "az"
                })

                az_cmds = []

                for r in result:

                    az_cmds.append(json.loads(r['text']))

                pass


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
    

if __name__ == "__main__":
    import asyncio

    async def main():
        azcli_tool_instance = await AzCliTool()
        result = await azcli_tool_instance.ainvoke(
            {'prompt': "Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size."}
        )
        print(result)

    asyncio.run(main())



    '{"status":200,'
    '"message":"Success",'
    '"results":{'
    '"command":"{\\u0022data\\u0022: [{\\u0022scenario\\u0022: \\u0022Create a virtual machine named \\u0027myVM\\u0027 in resource group \\u0027myResourceGroup\\u0027 with UbuntuLTS image and Standard_DS1_v2 size.\\u0022, \\u0022description\\u0022: \\u0022Create a virtual machine named \\u0027myVM\\u0027 in the specified resource group with UbuntuLTS image and Standard_DS1_v2 size, generating SSH keys for access.\\u0022, \\u0022commandSet\\u0022: [{\\u0022reason\\u0022: \\u0022Create a virtual machine with specified parameters including image and size.\\u0022, \\u0022example\\u0022: \\u0022az vm create --resource-group myResourceGroup --name myVM --image Ubuntu2204 --size Standard_DS1_v2 --generate-ssh-keys\\u0022, \\u0022command\\u0022: \\u0022az vm create\\u0022, \\u0022arguments\\u0022: [\\u0022--resource-group\\u0022, \\u0022--name\\u0022, \\u0022--image\\u0022, \\u0022--size\\u0022, \\u0022--generate-ssh-keys\\u0022]}]}], \\u0022error\\u0022: null, \\u0022status\\u0022: 200, \\u0022api_version\\u0022: \\u00221.0.0-prod-20251020.1\\u0022}",'
    '"cliType":"az"},'
    '"duration":0}'
