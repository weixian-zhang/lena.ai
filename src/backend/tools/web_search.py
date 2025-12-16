import asyncio
from pydantic import BaseModel
from browser_use import Agent, ChatAzureOpenAI, Browser
import os
from dotenv import load_dotenv
from tavily import TavilyClient
load_dotenv()

class WebSearchResult(BaseModel):
    result: str

# Initialize the model
llm = ChatAzureOpenAI(
    model="gpt-4o", # or your specific model deployment name
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)


# Create agent with the model
agent = Agent(
    task="""
    1. Go to google.com and search for Azure Kusto query to perform Azure Sentinel threat hunting on <search_query>.
    2. Visit top 3 search results links to find the most relevant Kusto query.
    
    <search_query>
    Azure kusto query for: Analyze trend analysis of Entra ID sign-in logs to detect unusual location changes for users across applications by computing trend lines of location diversity.
    It highlights the top three accounts with the steepest increase in location variability and lists their associated locations within 21-day windows.
    </search_query>

    <output>
    Extract the most relevant Kusto query from the search results and provide it as the final answer. Only provide the Kusto query as the output without any additional explanation or text.
    </output>
    """,
    llm=llm,
    browser=Browser(
        headless=True
    ),
    output_model_schema=WebSearchResult
)

# try Azure doc

def tavily_search():
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = tavily_client.search("""Azure kusto query for: Analyze trend analysis of Entra ID sign-in logs to detect unusual location changes for users across applications by computing trend lines of location diversity.
    It highlights the top three accounts with the steepest increase in location variability and lists their associated locations within 21-day windows.""")

    print(response)

async def main():
    # wsr: WebSearchResult = await agent.run()
    # print(wsr.result)

    tavily_search()

if __name__ == "__main__":
    asyncio.run(main())



''[Skip to main content](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#main)
[Skip to Ask Learn chat experience](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#). 
[Sign in](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#). 
![Image 1](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries).
![Image 2](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries).
[Profile](https://learn.microsoft.com/en-us/users/me/activity/).
[Settings](https://learn.microsoft.com/en-us/users/me/settings/). 
[Sign out](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#).
[Sign in](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#).
 ![Image 3](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). !
 [Image 4](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). *  
   [Profile](https://learn.microsoft.com/en-us/users/me/activity/). *  
     [Settings](https://learn.microsoft.com/en-us/users/me/settings/). [
         Sign out](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#). *
                      [Networking](https://learn.microsoft.com/en-us/azure/?product=networking). *   [Networking](https://learn.microsoft.com/en-us/azure/?product=networking). *   [Overview](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-overview). *   [Run KQL queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-queries). *   [Sample KQL queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). *   [Create KQL jobs](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-jobs). *   [Manage KQL jobs](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-manage-jobs). *   [Troubleshoot KQL for the lake](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-troubleshoot). Table of contents[Read in English](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries)Add to Collections Add to plan[Edit](https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/sentinel/datalake/kql-sample-queries.md). You can try [signing in](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#) or [changing directories](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). You can try [changing directories](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). 1.   [Out of the box queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#out-of-the-box-queries). 2.   [Additional sample queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#additional-sample-queries). 3.   [Sample queries for KQL jobs](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#sample-queries-for-kql-jobs). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#out-of-the-box-queries). For more information, see [Run KQL queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-queries#out-of-the-box-queries). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#anomalous-sign-in-locations-increase). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#anomalous-sign-in-behavior-based-on-location-changes). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#audit-rare-activity-by-app). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#azure-rare-subscription-level-operations). For operations lists, please refer to https://learn.microsoft.com/en-us/Azure/role-based-access-control/resource-provider-operations#all. [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-activity-trend-by-app-in-auditlogs). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-location-trend-per-user-or-app-in-signinlogs). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-network-traffic-trend-per-destination-ip). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-network-traffic-trend-per-destination-ip-with-data-transfer-stats). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-network-traffic-trend-per-source-ip). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-network-traffic-trend-per-source-ip-with-data-transfer-stats). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-sign-in-location-trend-per-user-and-app). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-process-execution-trend). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#entra-id-rare-user-agent-per-app). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#network-log-ioc-matching). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#new-processes-observed-in-last-24-hours). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#sharepoint-file-operation-via-previously-unseen-ips). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#palo-alto-potential-network-beaconing). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#windows-suspicious-login-outside-normal-hours). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#additional-sample-queries). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#identify-possible-insider-threats). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#investigate-potential-privilege-escalation-or-unauthorized-administrative-actions). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#investigate-slow-brute-force-attack). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#sample-queries-for-kql-jobs). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#brute-force-attack-incident-investigation). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#historical-activity-involving-ip-addresses-from-threat-intelligence). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#suspicious-travel-activity). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-sign-in-baseline). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-location-trend-per-user-and-application). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-process-execution-trend-1). 1.   [Out of the box queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#out-of-the-box-queries). 2.   [Additional sample queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#additional-sample-queries). 3.   [Sample queries for KQL jobs](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#sample-queries-for-kql-jobs). [Sign in](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#).'