# from langchain_core.tools import tool, Tool, BaseTool
# # from mcp import ClientSession, StdioServerParameters, types
# # from langchain_mcp_adapters.tools import load_mcp_tools
# # from mcp.client.stdio import stdio_client
# from pydantic import BaseModel, Field
# from typing import Type
# import json
# from tools.azure_mcp import az_cli_command_tool


# class AzCliToolSchema(BaseModel):
#     prompt: str = Field(description="'The user intent of the task to be solved by using the CLI tool. This user intent will be used to generate the appropriate CLI command to accomplish the desirable goal.'")


# class AzCliToolResult(BaseModel):
#     prompt: str = Field(default='', description="'The user intent of the task to be solved by using the CLI tool.'")
#     success: bool = Field(default=False, description="'Indicates whether the Azure CLI command was generated successfully.'")
#     az_commands: list[str] = Field(default=[], description="'The generated Azure CLI command as a string.'")
#     error: str = Field(default='', description="'Error message if the command generation failed.'")

# class AzCliTool(BaseTool):
#     """
#     A class to generate Azure CLI commands for managing resources.
#     """
#     name: str = "azure_cli_command_generator"
#     description: str = "'This tool can generate Azure CLI commands to accomplish a goal described by the user. This tool incorporates knowledge of the CLI tool beyond what the LLM knows. Always use this tool to generate the CLI command when the user asks for such CLI commands or wants to use the CLI tool to accomplish something.'"
#     args_schema: Type[BaseModel] = AzCliToolSchema
    

#     def _run(self, prompt: str) -> AzCliToolResult:
#         """The synchronous method that the agent will call."""
#         # This is where your custom logic or API call goes
#         raise NotImplementedError("Synchronous execution is not implemented. Please use the asynchronous method '_arun'.")

#     async def _arun(self, prompt: str) -> AzCliToolResult:
#         """The asynchronous method for the tool (optional)."""

#         try:
            
#             async with az_cli_command_tool() as azcli_tool:
                    
#                 result = await azcli_tool.ainvoke(input={
#                     "intent": prompt,
#                     "cli-type": "az"
#                 })

#                 azcli_result = AzCliToolResult()

#                 for r in result:
#                     td = json.loads(r['text'])
#                     azcli_result.success = True if td.get('message', '').lower() == 'success' else False
#                     command_data = td.get('results', '').get('command', '{}')
#                     command_data = json.loads(command_data)

#                     for cd in command_data.get('data', []):
#                         for cs in cd.get('commandSet', []):
#                             azcli_result.az_commands.append(cs.get('example', ''))

#                 return azcli_result
            
#         except Exception as e:
#             azcli_result = AzCliToolResult(success=False, 
#                                            az_commands=[],
#                                            error=str(e))

        

#     def _add_event_internal(self, summary, start, end):
#         # Your internal business logic
#         return f"Internal success for {summary}"
    
#     async def _add_event_internal_async(self, summary, start, end):
#         # Your internal async business logic
#         return f"Async internal success for {summary}"
    

# if __name__ == "__main__":
#     import asyncio

#     prompt_1 = """
#             create a virtual network named 'myVNet' in resource group 'myResourceGroup' with address prefix 172.15.0.0/16 and a subnet named 'mySubnet' with address prefix 172.15.1.0/24.
#             Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size and in virtual network myVNet.
#              """
    
#     prompt_2 = "update Storage account with name 'strgcwhd', set Allow storage account key access to true."

#     async def main():
#         azcli_tool_instance = AzCliTool()
#         result = await azcli_tool_instance.ainvoke(
#             {'prompt': prompt_2}
#         )
#         print(result)

#     asyncio.run(main())



