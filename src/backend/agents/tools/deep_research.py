import asyncio
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework import MagenticBuilder
from typing import cast
from agent_framework import (
    MAGENTIC_EVENT_TYPE_AGENT_DELTA, MAGENTIC_EVENT_TYPE_ORCHESTRATOR,
    AgentRunUpdateEvent,
    ChatMessage,
    WorkflowOutputEvent
)
# from dotenv import load_dotenv
# load_dotenv()

class DeepResearchToolResult(BaseModel):
    result: str = Field(description="The result of the deep web research.")

class DeepResearchToolInput(BaseModel):
    query: str = Field(description="The user query for deep web research.")

class DeepResearchTool(BaseTool):
    name: str = "deep_research_tool"
    description: str = "A tool that can access the Internet to conduct deep web search on a given user query using web searches and information gathering."
    args_schema: Type[BaseModel] = DeepResearchToolInput
    response_format: Type[BaseModel] = DeepResearchToolResult


    def _run(self, prompt: str) -> DeepResearchToolResult:
        """The synchronous method that the agent will call."""
        # This is where your custom logic or API call goes
        raise NotImplementedError("Synchronous execution is not implemented. Please use the asynchronous method '_arun'.")


    async def _arun(self, prompt: str) -> DeepResearchToolResult:
        """The asynchronous method for the tool (optional)."""

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
                .participants(researcher=researcher_agent) #, coder=coder_agent)
                .with_standard_manager(
                    agent=manager_agent,
                    max_round_count=10,  # Maximum collaboration rounds
                    max_stall_count=3,   # Maximum rounds without progress
                    max_reset_count=2,   # Maximum plan resets allowed
                )
            .build()
        )

        # State for streaming callback
        last_stream_agent_id: str | None = None
        stream_line_open: bool = False
        output: str | None = None

        async for event in workflow.run_stream(prompt):
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

        return DeepResearchToolResult(result=output if output else "")
    

async def main():
    dst = DeepResearchTool()
    result = await dst._arun("Research the latest advancements in AI for healthcare.")
    print(f"Deep Research Result: {result.result}")

if __name__ == "__main__":
    asyncio.run(main())