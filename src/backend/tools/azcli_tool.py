from langchain_core.tools import tool, Tool
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

class AzCliTool:
    """
    A class to generate Azure CLI commands for managing resources.
    """
    def __init__(self):
        self.azcli_tool: Tool = None

    @classmethod
    async def create(cls):
        self = cls()
        azcli_tool = await self._load_azure_mcp_azcli_tool()
        self.azcli_tool = azcli_tool
        return self
    
    async def _load_azure_mcp_azcli_tool(self) -> Tool:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@azure/mcp@latest", "server", "start"],
            env=None
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List available tools
                tools = await session.list_tools()
                for tool in tools.tools: print(tool.name)

                # Format tools for Azure OpenAI
                tools = [tool for tool in tools.tools if tool.name == "extension_cli_generate"]
        
        assert tools is not None, "No tools found from MCP session."
        assert len(tools) == 1, "Expected exactly one Azure CLI generation tool."

        return tools[0]

    @tool
    def generate_execute_azure_cli_command(self, prompt: str) -> dict:
        """
        This tool can generate Azure CLI commands to be used with the corresponding CLI tool to accomplish a goal described by the user. This tool incorporates knowledge of the CLI tool beyond what the LLM knows. Always use this tool to generate the CLI command when the user asks for such CLI commands or wants to use the CLI tool to accomplish something.

        :param prompt: a prompt to describe Azure operation to be performed and its parameters preferably. The Azure CLI command will be genrated internally for example: az vm create --resource-group myResourceGroup --name myVM --image UbuntuLTS --size Standard_DS1_v2
        :return: dictionary of Azure CLI command execution result
        """

        cmd = self.azcli_tool.invoke({"intent": prompt})
        return {}
    

if __name__ == "__main__":
    import asyncio

    async def main():
        azcli_tool_instance = await AzCliTool.create()
        result = azcli_tool_instance.generate_execute_azure_cli_command.invoke(
            {'prompt': "Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size."}
        )
        print(result)

    asyncio.run(main())
