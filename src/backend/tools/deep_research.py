import asyncio
from pydantic import BaseModel

from agent_framework import ChatAgent, HostedCodeInterpreterTool
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.openai import  OpenAIChatClient, OpenAIResponsesClient
from agent_framework import MagenticBuilder
from typing import cast
from agent_framework import (
    MAGENTIC_EVENT_TYPE_AGENT_DELTA, MAGENTIC_EVENT_TYPE_ORCHESTRATOR,
    AgentRunUpdateEvent,
    ChatMessage,
    WorkflowOutputEvent
)


# original langchain
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
load_dotenv()

class WebSearchResult(BaseModel):
    result: str

# Initialize the model
# llm = ChatAzureOpenAI(
#     model="gpt-4o", # or your specific model deployment name
#     api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
# )

test_prompt_1 = """Azure kusto query for: Analyze trend analysis of Entra ID sign-in logs to detect unusual location changes for users across applications by computing trend lines of location diversity.
    It highlights the top three accounts with the steepest increase in location variability and lists their associated locations within 21-day windows."""

test_prompt_2 = "azure kusto query"

# Create agent with the model
# agent = Agent(
#     task="""
#     1. Go to google.com and search for Azure Kusto query to perform Azure Sentinel threat hunting on <search_query>.
#     2. Visit top 3 search results links to find the most relevant Kusto query.
    
#     <search_query>
#     Azure kusto query for: Analyze trend analysis of Entra ID sign-in logs to detect unusual location changes for users across applications by computing trend lines of location diversity.
#     It highlights the top three accounts with the steepest increase in location variability and lists their associated locations within 21-day windows.
#     </search_query>

#     <output>
#     Extract the most relevant Kusto query from the search results and provide it as the final answer. Only provide the Kusto query as the output without any additional explanation or text.
#     </output>
#     """,
#     llm=llm,
#     browser=Browser(
#         headless=True
#     ),
#     output_model_schema=WebSearchResult
# )


# async def search_azure_doc():

#     azmcp = AzureMcpTools()
    
#     # try Azure doc
#     async with azmcp.az_mcp_session() as session:

#         # Load the MCP tools into a list of LangChain BaseTool objects
#         langchain_tools: list[BaseTool] = await load_mcp_tools(session)

#         # Format tools for Azure OpenAI
#         tools = [tool for tool in langchain_tools if tool.name == 'documentation']

#         assert tools, "Error at Azure MCP tools, no Azure CLI generation tool found."
#         assert len(tools) == 1, "Error at Azure MCP tools, expected exactly one Azure CLI generation tool."

#         tool = tools[0]

#         mcp_result = await tool.ainvoke(input={
#                 "intent": test_prompt_2,
#                 "command": "microsoft_code_sample_search",
#                 "learn": False
#             })
        
#         pass


# # tavily search
# def tavily_search():
#     tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
#     response = tavily_client.search(
#         query=test_prompt_1,
#         max_results=5,
#         search_depth="advanced"
#     )

#     search_result = '\n\n'.join([r['content'] for r in response['results']])

#     llm = AzureChatOpenAI(
#                     deployment_name="gpt-4o",
#                     model="gpt-4o",
#                     api_version="2024-12-01-preview",
#                     temperature=0.0
#                 )
    
#     messages = [
#         SystemMessage(content=f"""You are an expert Azure documentation assistant.
#         Given the following search results from Tavily, extract and format the most relevant Azure CLI command according to the <web_search_result> provided.
        
#         <web_search_result>
#         {search_result}
#         </web_search_result>

#         <output>
#         Only output a single Azure CLI command that best fits the user request and nothing else, no explanation needed.
#         </output>

#         """),
#         HumanMessage(content=f"""From the above search results, extract and format the most relevant Azure CLI command for the following request:
#         {test_prompt_1}"""
#         )
#     ]

#     response = llm.invoke(input=messages)
    
#     print(response)


async def magentic_deep_research():
    
    researcher_agent = ChatAgent(
        name="ResearcherAgent",
        description="Specialist in research and information gathering",
        instructions=(
            "You are a Researcher. You find information without additional computation or quantitative analysis."
        ),
        # This agent requires the gpt-4o-search-preview model to perform web searches
        chat_client=AzureOpenAIChatClient(
            deployment_name="gpt-4o",
            api_version="2024-12-01-preview"
        )
    )

    coder_agent = ChatAgent(
        name="CoderAgent",
        description="A helpful assistant that writes and executes code to process and analyze data.",
        instructions="You solve questions using code. Please provide detailed analysis and computation process.",
        chat_client=AzureOpenAIChatClient(
            deployment_name="gpt-4o",
            api_version="2024-12-01-preview"
        ),
        tools=HostedCodeInterpreterTool(),
    )

    # Create a manager agent for orchestration
    manager_agent = ChatAgent(
        name="MagenticManager",
        description="Orchestrator that coordinates the research and coding workflow",
        instructions="You coordinate a team to complete complex tasks efficiently.",
        chat_client=AzureOpenAIChatClient(
            deployment_name="gpt-4o",
            api_version="2024-12-01-preview"
        )
    )

    workflow = (
        MagenticBuilder()
            .participants(researcher=researcher_agent, coder=coder_agent)
            .with_standard_manager(
                agent=manager_agent,
                max_round_count=10,  # Maximum collaboration rounds
                max_stall_count=3,   # Maximum rounds without progress
                max_reset_count=2,   # Maximum plan resets allowed
            )
        .build()
    )

    task = (
        """
        <task>
        Azure kusto query for Azure Sentinel to: Analyze trend analysis of Entra ID sign-in logs to detect unusual location changes for users across applications by computing trend lines of location diversity.
        It highlights the top three accounts with the steepest increase in location variability and lists their associated locations within 21-day windows.
        </task>

        <output>
        Provide the final Azure Kusto query as the output. Only provide the Kusto query without any additional explanation or text.
        </output>
    """
    )

    # State for streaming callback
    last_stream_agent_id: str | None = None
    stream_line_open: bool = False
    output: str | None = None

    async for event in workflow.run_stream(task):
        if isinstance(event, AgentRunUpdateEvent):
            props = event.data.additional_properties if event.data else None
            event_type = props.get("magentic_event_type") if props else None

            if event_type == MAGENTIC_EVENT_TYPE_ORCHESTRATOR:
                # Manager's planning and coordination messages
                kind = props.get("orchestrator_message_kind", "") if props else ""
                text = event.data.text if event.data else ""
                print(f"\n[ORCH:{kind}]\n\n{text}\n{'-' * 26}")

            elif event_type == MAGENTIC_EVENT_TYPE_AGENT_DELTA:
                # Streaming tokens from agents
                agent_id = props.get("agent_id", event.executor_id) if props else event.executor_id
                if last_stream_agent_id != agent_id or not stream_line_open:
                    if stream_line_open:
                        print()
                    print(f"\n[STREAM:{agent_id}]: ", end="", flush=True)
                    last_stream_agent_id = agent_id
                    stream_line_open = True
                if event.data and event.data.text:
                    print(event.data.text, end="", flush=True)

            elif event.data and event.data.text:
                print(event.data.text, end="", flush=True)

        elif isinstance(event, WorkflowOutputEvent):
            output_messages = cast(list[ChatMessage], event.data)
            if output_messages:
                output = output_messages[-1].text

    if stream_line_open:
        print()

    if output is not None:
        print(f"Workflow completed with result:\n\n{output}")
    

async def main():
    # wsr: WebSearchResult = await agent.run()
    # print(wsr.result)

    # tavily_search()

    #await search_azure_doc()

    await magentic_deep_research()

if __name__ == "__main__":
    asyncio.run(main())


"```\nSigninLogs | where CreatedDateTime >= ago(21d) | summarize locationCount = dcount(Location) by UserPrincipalName, AppDisplayName | extend trend = series_decompose_anomalies(locationCount, 0.5, -1, 'linefit') | where trend > 0 | top 3 by trend desc | project UserPrincipalName, AppDisplayName, locationCount\n```"

# 'Here are the available command and their parameters for \'documentation\' tool.\n'
# 'If you do not find a suitable command, run again with the "learn=true" to get a list of available commands and their parameters.\n'
# 'Next, identify the command you want to execute and run again with the "command" and "parameters" arguments.\n\n'
# '[{"name":"microsoft_docs_search","title":"Microsoft Docs Search","description":"Search official Microsoft/Azure documentation to find the most relevant and trustworthy content for a user\\u0027s query. This tool returns up to 10 high-quality content chunks (each max 500 tokens), extracted from Microsoft Learn and other official sources. Each result includes the article title, URL, and a self-contained content excerpt optimized for fast retrieval and reasoning. Always use this tool to quickly ground your answers in accurate, first-party Microsoft/Azure knowledge.\\n\\nThe \\u0060question\\u0060 parameter is no longer used, use \\u0060query\\u0060 instead.\\n\\n## Follow-up Pattern\\nTo ensure completeness, use microsoft_docs_fetch when high-value pages are identified by search. The fetch tool complements search by providing the full detail. This is a required step for comprehensive results.","inputSchema":{"type":"object","properties":{"query":{"description":"a query or topic about Microsoft/Azure products, services, platforms, developer tools, frameworks, or APIs","type":"string","default":null},"question":{"description":"this parameter is no longer used, use query instead.","type":"string","default":null}}},"outputSchema":{"type":"object","properties":{"results":{"type":"array","items":{"type":"object","properties":{"id":{"type":["string","null"]},"title":{"type":"string"},"content":{"type":"string"},"contentUrl":{"type":"string"},"extensionData":{"type":["object","null"]}}}}}},"annotations":{"title":"Microsoft Docs Search","destructiveHint":false,"idempotentHint":true,"readOnlyHint":true}},'
# '{"name":"microsoft_code_sample_search","title":"Microsoft Code Sample Search","description":"Search for code snippets and examples in official Microsoft Learn documentation. '
# 'This tool retrieves relevant code samples from Microsoft documentation pages providing developers with practical implementation examples and best practices for Microsoft/Azure products and services related coding tasks.'
# ' This tool will help you use the **LATEST OFFICIAL** code snippets to empower coding capabilities.\\n\\n## When to Use This Tool\\n- When you are going to provide sample Microsoft/Azure related code snippets in your answers.\\n- When you are **generating any Microsoft/Azure related code**.\\n\\n## Usage Pattern\\nInput a descriptive query, or SDK/class/method name to retrieve related code samples. The optional parameter \\u0060language\\u0060 can help to filter results.\\n\\nEligible values for \\u0060language\\u0060 parameter include: csharp javascript typescript python powershell azurecli al sql java kusto cpp go rust ruby php","inputSchema":{"type":"object","properties":{"query":{"description":"a descriptive query, SDK name, method name or code snippet related to Microsoft/Azure products, services, platforms, developer tools, frameworks, APIs or SDKs","type":"string"},"language":{"description":"Optional parameter specifying the programming language of code snippets to retrieve. Can significantly improve search quality if provided. Eligible values: csharp javascript typescript python powershell azurecli al sql java kusto cpp go rust ruby php","type":"string","default":null}},"required":["query"]},"outputSchema":{"type":"object","properties":{"results":{"type":"array","items":{"type":"object","properties":{"description":{"type":"string"},"codeSnippet":{"type":"string"},"link":{"type":"string"},"language":{"type":"string"}}}}}},"annotations":{"title":"Microsoft Code Sample Search","destructiveHint":false,"idempotentHint":true,"readOnlyHint":true}},
# {"name":"microsoft_docs_fetch","title":"Microsoft Docs Fetch","description":"Fetch and convert a Microsoft Learn documentation page to markdown format. This tool retrieves the latest complete content of Microsoft documentation pages including Azure, .NET, Microsoft 365, and other Microsoft technologies.\\n\\n## When to Use This Tool\\n- When search results provide incomplete information or truncated content\\n- When you need complete step-by-step procedures or tutorials\\n- When you need troubleshooting sections, prerequisites, or detailed explanations\\n- When search results reference a specific page that seems highly relevant\\n- For comprehensive guides that require full context\\n\\n## Usage Pattern\\nUse this tool AFTER microsoft_docs_search when you identify specific high-value pages that need complete content. The search tool gives you an overview; this tool gives you the complete picture.\\n\\n## URL Requirements\\n- The URL must be a valid link from the microsoft.com domain.\\n\\n## Output Format\\nmarkdown with headings, code blocks, tables, and links preserved.","inputSchema":{"type":"object","properties":{"url":{"description":"URL of the Microsoft documentation page to read","type":"string"}},"required":["url"]},"annotations":{"title":"Microsoft Docs Fetch","destructiveHint":false,"idempotentHint":true,"readOnlyHint":true}}]'

# azure doc
# 'Here are the available command and their parameters for \'documentation\' tool.\n'
# 'If you do not find a suitable command, run again with the "learn=true" to get a list of available commands and their parameters.
#     Next, identify the command you want to execute and run again with the "command" and "parameters" arguments.'
#     '\n\n[{"name":"microsoft_docs_search","title":"Microsoft Docs Search","description":"Search official Microsoft/Azure documentation to find the most relevant and '
#     'trustworthy content for a user\\u0027s query. '
#     'This tool returns up to 10 high-quality content chunks (each max 500 tokens), extracted from Microsoft Learn and other official sources.'
#     'Each result includes the article title, URL, and a self-contained content excerpt optimized for fast retrieval and reasoning. '
#     'Always use this tool to quickly ground your answers in accurate, first-party Microsoft/Azure knowledge.\\n\\n'
#     'The \\u0060question\\u0060 parameter is no longer used, use \\u0060query\\u0060 instead.\\n\\n## Follow-up Pattern\\n'
#     'To ensure completeness, use microsoft_docs_fetch when high-value pages are identified by search. '
#     'The fetch tool complements search by providing the full detail. '
#     'This is a required step for comprehensive results.","inputSchema":{"type":"object","properties":{"query":{"description":"a query or topic about'
#     ' Microsoft/Azure products, services, platforms, developer tools, frameworks, or APIs","type":"string","default":null},"question":'
#     '{"description":"this parameter is no longer used, use query instead.","type":"string","default":null}}},"outputSchema":'
#     '{"type":"object","properties":{"results":{"type":"array","items":{"type":"object","properties":{"id":{"type":["string","null"]},"title":'
#     '{"type":"string"},"content":{"type":"string"},"contentUrl":{"type":"string"},"extensionData":{"type":["object","null"]}}}}}},"annotations":'
#     '{"title":"Microsoft Docs Search","destructiveHint":false,"idempotentHint":true,"readOnlyHint":true}},{"name":"microsoft_code_sample_search",'
#     '"title":"Microsoft Code Sample Search","description":"Search for code snippets and examples in official Microsoft Learn documentation. '
#     'This tool retrieves relevant code samples from Microsoft documentation pages providing developers with practical implementation examples and'
#     'best practices for Microsoft/Azure products and services related coding tasks. '
#     'This tool will help you use the **LATEST OFFICIAL** code snippets to empower coding capabilities.'
#     'When to Use This Tool\\n- When you are going to provide sample Microsoft/Azure related code snippets in your answers.\\n- '
#     'When you are **generating any Microsoft/Azure related code**.\\n\\n## Usage Pattern\\nInput a descriptive query, or '
#     'SDK/class/method name to retrieve related code samples. The optional parameter \\u0060language\\u0060 can help to filter results.\\n\\n'
#     'Eligible values for \\u0060language\\u0060 parameter include: csharp javascript typescript python powershell azurecli al sql java kusto cpp go rust ruby php","inputSchema":{"type":"object","properties":{"query":{"description":"a descriptive query, SDK name, method name or code snippet related to Microsoft/Azure products, services, platforms, developer tools, frameworks, APIs or SDKs","type":"string"},"language":{"description":"Optional parameter specifying the programming language of code snippets to retrieve. Can significantly improve search quality if provided. Eligible values: csharp javascript typescript python powershell azurecli al sql java kusto cpp go rust ruby php","type":"string","default":null}},"required":["query"]},"outputSchema":{"type":"object","properties":{"results":{"type":"array","items":{"type":"object","properties":{"description":{"type":"string"},"codeSnippet":{"type":"string"},"link":{"type":"string"},"language":{"type":"string"}}}}}},"annotations":{"title":"Microsoft Code Sample Search","destructiveHint":false,"idempotentHint":true,"readOnlyHint":true}},{"name":"microsoft_docs_fetch","title":"Microsoft Docs Fetch","description":"Fetch and convert a Microsoft Learn documentation page to markdown format. This tool retrieves the latest complete content of Microsoft documentation pages including Azure, .NET, Microsoft 365, and other Microsoft technologies.\\n\\n## When to Use This Tool\\n- When search results provide incomplete information or truncated content\\n- When you need complete step-by-step procedures or tutorials\\n- When you need troubleshooting sections, prerequisites, or detailed explanations\\n- When search results reference a specific page that seems highly relevant\\n- For comprehensive guides that require full context\\n\\n## Usage Pattern\\nUse this tool AFTER microsoft_docs_search when you identify specific high-value pages that need complete content. The search tool gives you an overview; this tool gives you the complete picture.\\n\\n## URL Requirements\\n- The URL must be a valid link from the microsoft.com domain.\\n\\n## Output Format\\nmarkdown with headings, code blocks, tables, and links preserved.","inputSchema":{"type":"object","properties":{"url":{"description":"URL of the Microsoft documentation page to read","type":"string"}},"required":["url"]},"annotations":{"title":"Microsoft Docs Fetch","destructiveHint":false,"idempotentHint":true,"readOnlyHint":true}}]'

# ''[Skip to main content](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#main)
# [Skip to Ask Learn chat experience](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#). 
# [Sign in](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#). 
# ![Image 1](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries).
# ![Image 2](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries).
# [Profile](https://learn.microsoft.com/en-us/users/me/activity/).
# [Settings](https://learn.microsoft.com/en-us/users/me/settings/). 
# [Sign out](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#).
# [Sign in](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#).
#  ![Image 3](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). !
#  [Image 4](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). *  
#    [Profile](https://learn.microsoft.com/en-us/users/me/activity/). *  
#      [Settings](https://learn.microsoft.com/en-us/users/me/settings/). [
#          Sign out](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#). *
#                       [Networking](https://learn.microsoft.com/en-us/azure/?product=networking). *   [Networking](https://learn.microsoft.com/en-us/azure/?product=networking). *   [Overview](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-overview). *   [Run KQL queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-queries). *   [Sample KQL queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). *   [Create KQL jobs](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-jobs). *   [Manage KQL jobs](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-manage-jobs). *   [Troubleshoot KQL for the lake](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-troubleshoot). Table of contents[Read in English](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries)Add to Collections Add to plan[Edit](https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/sentinel/datalake/kql-sample-queries.md). You can try [signing in](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#) or [changing directories](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). You can try [changing directories](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries). 1.   [Out of the box queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#out-of-the-box-queries). 2.   [Additional sample queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#additional-sample-queries). 3.   [Sample queries for KQL jobs](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#sample-queries-for-kql-jobs). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#out-of-the-box-queries). For more information, see [Run KQL queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-queries#out-of-the-box-queries). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#anomalous-sign-in-locations-increase). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#anomalous-sign-in-behavior-based-on-location-changes). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#audit-rare-activity-by-app). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#azure-rare-subscription-level-operations). For operations lists, please refer to https://learn.microsoft.com/en-us/Azure/role-based-access-control/resource-provider-operations#all. [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-activity-trend-by-app-in-auditlogs). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-location-trend-per-user-or-app-in-signinlogs). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-network-traffic-trend-per-destination-ip). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-network-traffic-trend-per-destination-ip-with-data-transfer-stats). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-network-traffic-trend-per-source-ip). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-network-traffic-trend-per-source-ip-with-data-transfer-stats). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-sign-in-location-trend-per-user-and-app). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-process-execution-trend). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#entra-id-rare-user-agent-per-app). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#network-log-ioc-matching). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#new-processes-observed-in-last-24-hours). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#sharepoint-file-operation-via-previously-unseen-ips). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#palo-alto-potential-network-beaconing). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#windows-suspicious-login-outside-normal-hours). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#additional-sample-queries). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#identify-possible-insider-threats). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#investigate-potential-privilege-escalation-or-unauthorized-administrative-actions). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#investigate-slow-brute-force-attack). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#sample-queries-for-kql-jobs). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#brute-force-attack-incident-investigation). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#historical-activity-involving-ip-addresses-from-threat-intelligence). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#suspicious-travel-activity). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-sign-in-baseline). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-location-trend-per-user-and-application). [](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#daily-process-execution-trend-1). 1.   [Out of the box queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#out-of-the-box-queries). 2.   [Additional sample queries](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#additional-sample-queries). 3.   [Sample queries for KQL jobs](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#sample-queries-for-kql-jobs). [Sign in](https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-sample-queries#).'