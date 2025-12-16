from tools.az_shell import AzShell, AzShellResult
from tools.az_cli_tool import AzCliTool, AzCliToolResult

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

    sentinel_threat_hunting_prompt_1 = """
generate Azure Kusto query to below requirement:
Analyze trend analysis of Entra ID sign-in logs to detect unusual location changes for users across applications by computing trend lines of location diversity. It highlights the top three accounts with the steepest increase in location variability and lists their associated locations within 21-day windows.
"""

    sentinel_threat_hunting_prompt_2 = """
** tool scratchpad **:

kusto query to analyze trend analysis of Entra ID sign-in logs to detect unusual location changes for users across applications by computing trend lines of location diversity. It highlights the top three accounts with the steepest increase in location variability and lists their associated locations within 21-day windows.:

// Define the time window for analysis
let timeWindow = 21d;
let trendWindow = 7d; // Define a shorter window for trend calculation, e.g., weekly trends

SigninLogs
| where TimeGenerated >= ago(timeWindow)
// Focus on successful sign-ins as a baseline for normal user activity
| where ResultType == "0"
// Filter out sign-ins with empty location details
| where isnotempty(LocationDetails.city) or isnotempty(LocationDetails.countryOrRegion)

// Pre-process and summarize location diversity over daily intervals for each user and application
| summarize DailyLocations = dcountif(strcat(LocationDetails.countryOrRegion, " - ", LocationDetails.city), isnotempty(LocationDetails.city) or isnotempty(LocationDetails.countryOrRegion)) by UserPrincipalName, AppDisplayName, bin(TimeGenerated, 1d)
| order by UserPrincipalName, AppDisplayName, TimeGenerated asc

// Generate a time series of location counts
| summarize LocationCountSeries = make_list(DailyLocations, TimeGenerated) by UserPrincipalName, AppDisplayName

// Use the trend_line operator to calculate the trend of location diversity
// This is a conceptual step as KQL doesn't have a direct 'trend_line' operator like that.
// The common approach for trend is using time series analysis (series_fit_line, series_fit_poly)
// The following is a common KQL approach to find anomalous behavior using the built-in ML operators.
// A simpler, more direct approach to the requirement is to use a windowed count and compare the recent count to an average.

// Alternative approach: Calculate location variability in two separate windows (last 7 days vs previous 14 days)


let recentLocations = SigninLogs
| where TimeGenerated >= ago(trendWindow)
| where ResultType == "0"
| summarize RecentDistinctLocations = dcountif(strcat(LocationDetails.countryOrRegion, " - ", LocationDetails.city), isnotempty(LocationDetails.city) or isnotempty(LocationDetails.countryOrRegion)) by UserPrincipalName, AppDisplayName;

let pastLocations = SigninLogs
| where TimeGenerated >= ago(timeWindow) and TimeGenerated < ago(trendWindow)
| where ResultType == "0"
| summarize PastDistinctLocations = dcountif(strcat(LocationDetails.countryOrRegion, " - ", LocationDetails.city), isnotempty(LocationDetails.city) or isnotempty(LocationDetails.countryOrRegion)) by UserPrincipalName, AppDisplayName;

// Join the two results to compare
recentLocations
| join kind=inner (pastLocations) on UserPrincipalName, AppDisplayName
// Calculate the increase in location diversity
| extend LocationIncrease = RecentDistinctLocations - PastDistinctLocations
// Filter for users where the recent distinct locations are significantly more than past locations
| where RecentDistinctLocations > 1.5 * PastDistinctLocations and RecentDistinctLocations > 2 // Ensure it's a significant jump and not just a jump from 0 to 1
| order by LocationIncrease desc
// Get the top 3 users
| top 3 by LocationIncrease desc

// Join back to the original logs to list the associated locations within the 21-day window
| join kind=inner (
    SigninLogs
    | where TimeGenerated >= ago(timeWindow)
    | where ResultType == "0"
    | extend Location = strcat(LocationDetails.countryOrRegion, " - ", LocationDetails.city)
    | where isnotempty(Location)
    | distinct UserPrincipalName, AppDisplayName, Location
) on UserPrincipalName, AppDisplayName

| project UserPrincipalName, AppDisplayName, RecentDistinctLocations, PastDistinctLocations, LocationIncrease, Location
| summarize LocationsList = make_set(Location) by UserPrincipalName, AppDisplayName, RecentDistinctLocations, PastDistinctLocations, LocationIncrease
| project-away PastDistinctLocations, RecentDistinctLocations // Tidy up the final output
| order by LocationIncrease desc


** instructions **
given data in <tool scratchpad> try format it to the best of your knowledge Azure CLI command without using tool.
!output only the command and nothing else in format for example: az monitor query
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

        ai_msg: AIMessage = llm.invoke(input=sentinel_threat_hunting_prompt_2)


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
