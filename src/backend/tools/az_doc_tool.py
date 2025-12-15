from langchain_core.tools import tool, Tool, BaseTool
from pydantic import BaseModel, Field
from typing import Type
import json
from tools.util_az_mcp import az_doc_tool

class AzDocToolSchema(BaseModel):
    prompt: str = Field(description="Search official Microsoft/Azure documentation to find the most relevant and trustworthy content for a user\'s query. This tool returns up to 10 high-quality content chunks (each max 500 tokens), extracted from Microsoft Learn and other official sources. Each result includes the article title, URL, and a self-contained content excerpt optimized for fast retrieval and reasoning. Always use this tool to quickly ground your answers in accurate, first-party Microsoft/Azure knowledge.This tool is a hierarchical MCP command router.\nSub commands are routed to MCP servers that require specific fields inside the \"parameters\" object.\nTo invoke a command, set \"command\" and wrap its args in \"parameters\".\nSet \"learn=true\" to discover available sub commands.")

class AzDocToolResult(BaseModel):
    success: bool = Field(default=False, description="Indicates whether the Azure documentation search was successful.")
    documents: list[str] = Field(default=[], description="The retrieved documentation content chunks as a list of strings.")
    error: str = Field(default='', description="Error message if the documentation search failed.")

class AzCliTool(BaseTool):
    """
    A class to generate Azure CLI commands for managing resources.
    """
    name: str = "azure_documentation_search"
    description: str = "Search official Microsoft/Azure documentation to find the most relevant and trustworthy content for a user\'s query. This tool returns up to 10 high-quality content chunks (each max 500 tokens), extracted from Microsoft Learn and other official sources. Each result includes the article title, URL, and a self-contained content excerpt optimized for fast retrieval and reasoning. Always use this tool to quickly ground your answers in accurate, first-party Microsoft/Azure knowledge.This tool is a hierarchical MCP command router.\nSub commands are routed to MCP servers that require specific fields inside the \"parameters\" object.\nTo invoke a command, set \"command\" and wrap its args in \"parameters\".\nSet \"learn=true\" to discover available sub commands."
    args_schema: Type[BaseModel] = AzDocToolSchema


    def _run(self, prompt: str) -> AzDocToolResult:
        """The synchronous method that the agent will call."""
        # This is where your custom logic or API call goes
        raise NotImplementedError("Synchronous execution is not implemented. Please use the asynchronous method '_arun'.")

    async def _arun(self, prompt: str) -> AzDocToolResult:
        """The asynchronous method for the tool (optional)."""

        try:
            
            async with az_doc_tool() as azdoc_tool:
                    
                result = await azdoc_tool.ainvoke(input={
                    "intent": prompt,
                })

                azdoc_result = AzDocToolResult()

                for r in result:
                    td = json.loads(r['text'])
                    azdoc_result.success = True if td.get('message', '').lower() == 'success' else False
                    documents_data = td.get('results', '').get('documents', '[]')
                    documents_data = json.loads(documents_data)

                    for doc in documents_data:
                        azdoc_result.documents.append(f"Title: {doc.get('title', '')}\nURL: {doc.get('url', '')}\nContent: {doc.get('content', '')}\n")

                return azdoc_result
            
        except Exception as e:
            azdoc_result = AzDocToolResult(success=False, 
                                           documents=[],
                                           error=str(e))
            return azdoc_result


    def _add_event_internal(self, summary, start, end):
        # Your internal business logic
        return f"Internal success for {summary}"
    
    async def _add_event_internal_async(self, summary, start, end):
        # Your internal async business logic
        return f"Async internal success for {summary}"