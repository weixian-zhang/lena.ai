from tools.az_shell import AzShell, AzShellResult
from tools.azcli_cmd_tool import AzCliTool, AzCliToolResult
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
load_dotenv()


if __name__ == "__main__":
    import asyncio

    prompt_1 = """
            create a virtual network named 'myVNet' in resource group 'myResourceGroup' with address prefix 172.15.0.0/16 and a subnet named 'mySubnet' with address prefix 172.15.1.0/24.
            Create a virtual machine named 'myVM' in resource group 'myResourceGroup' with UbuntuLTS image and Standard_DS1_v2 size and in virtual network myVNet.
             """
    
    prompt_2 = "create a Storage account with name 'strgwodsissd' in resource group 'rg-common'. Also create private endpoint for this storage. Disable public network access.~"

    async def main():
        
        azcli_tool_instance = AzCliTool()
        result: AzCliToolResult = await azcli_tool_instance.ainvoke(
            {'prompt': prompt_2}
        )

        if result.success:

            shell = AzShell()

            for cmd in result.az_commands:
                
                shell_result: AzShellResult = await shell.run(cmd, timeout=5)

                if shell_result.success:
                    print(f"Command output:\n{shell_result.stdout}")
                else:
                    print(f"Command failed with error:\n{shell_result.stderr}")

    asyncio.run(main())