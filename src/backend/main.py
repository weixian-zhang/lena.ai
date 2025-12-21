from backend.tools.az_shell import AzShell, AzShellResult
from backend.tools.__bak_az_cli_tool import AzCliTool, AzCliToolResult

from tools.tools_manager import ToolManager
from dotenv import load_dotenv
load_dotenv()



if __name__ == "__main__":
    import asyncio

    azcli_prompt_1 = """
            create a virtual network named 'myVNet' in resource group 'myResourceGroup' with address prefix 172.15.0.0/16 and a subnet named 'mySubnet' with address prefix 172.15.1.0/24.
            Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size and in virtual network myVNet.
             """
    
    azcli_prompt_2 = "create a Storage account with name 'strgwodsissd' in resource group 'rg-common'. Also create private endpoint for this storage. Disable public network access.~"

    az_doc_prompt_1 = "what is the kusto query to get top 10 CPU consuming queries in last 1 hour for VM name vm1 in resource group rg1?"

    resource_search_prompt_1 = "how many public IPs are there that are not associated with any resource"

    web_search_sentinel_kusto_query_prompt_1 = """
    <task>
    Azure kusto query for Azure Sentinel to: Analyze trend analysis of Entra ID sign-in logs to detect unusual location changes for users across applications by computing trend lines of location diversity.
    It highlights the top three accounts with the steepest increase in location variability and lists their associated locations within 21-day windows.
    </task>

    <output>
    Provide the final Azure Kusto query as the output. Only provide the Kusto query without any additional explanation or text.
    </output>
    """

    async def main():
        import json
        from langchain_openai import AzureChatOpenAI
        from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
        from mcp import ClientSession, StdioServerParameters, stdio_client

        llm = AzureChatOpenAI(
                    deployment_name="gpt-4o",
                    model="gpt-4o",
                    api_version="2024-12-01-preview",
                    temperature=0.0
                )

        tm = await ToolManager.create()
        extension_cli_generate = tm.tools['extension_cli_generate'] #tm.tools['extension_cli_generate']
        llm = llm.bind_tools([extension_cli_generate])

        ai_msg: AIMessage = llm.invoke(input=web_search_sentinel_kusto_query_prompt_1)


        if ai_msg.tool_calls:
            tool_name = ai_msg.tool_calls[0]['name']
            tool_args = ai_msg.tool_calls[0]['args']


        try:
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@azure/mcp@latest", "server", "start"],
                env=None
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    result = await session.call_tool(tool_name, tool_args)
                    #result = await tm.tools[tool_name].ainvoke(input=tool_args)
            
            # result = await tm.tools[tool_name].ainvoke(input={
            #             "intent": resource_search_prompt_1,
            #             "cli-type": "az"
            #         })
            
                    commands = []
                    for r in result:
                        td = json.loads(result.content[0].text)
                        command_data = td.get('results', '').get('command', '{}')
                        command_data = json.loads(command_data)

                        for cd in command_data.get('data', []):
                            for cs in cd.get('commandSet', []):
                                commands.append(cs.get('example', ''))

                    shell = AzShell()
                    for cmd in commands:
                        result = await shell.run(cmd)
                        pass

        except Exception as e:
            print(f"Error: {str(e)}")


        # azcli_tool_instance = AzCliTool()
        # result: AzCliToolResult = await azcli_tool_instance.ainvoke(
        #     {'prompt': azcli_prompt_2}
        # )

        # if result.success:

        #     shell = AzShell()

        #     for cmd in result.az_commands:
                
        #         shell_result: AzShellResult = await shell.run(cmd, timeout=5)

        #         if shell_result.success:
        #             print(f"Command output:\n{shell_result.stdout}")
        #         else:
        #             print(f"Command failed with error:\n{shell_result.stderr}")

    asyncio.run(main())
