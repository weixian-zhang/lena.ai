from langgraph.types import interrupt, Command
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from prompt import missing_azure_values_system_prompt, update_user_prompt_with_filled_values_system_prompt
from state import ExecutionState, Agents
from utils import Util
import json


class ResolveValuesAgentOutput(BaseModel):
    required_values: dict[str, str] = Field(default={}, description="A dictionary containing the missing information for human to fill in")


class ValueResolverAgent:

    def check_for_missing_azure_values(self, execution_state: ExecutionState) -> dict:

        llm: AzureChatOpenAI = Util.gpt_4o()

        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=missing_azure_values_system_prompt),
                HumanMessage(content=execution_state.scratchpad.original_prompt)
            ]   
        )

        missing_info_chain = chat_template | llm

        # filled will be populated by human-in-the-loop (later)
        filled_values = execution_state.scratchpad.missing_azure_values_in_prompt.filled

        response = missing_info_chain.invoke(input={"filled_missing_values": filled_values})

        if response.content.strip() != "{}":
            missing_values: dict[str, str] = json.loads(response.content.strip())
            execution_state.scratchpad.missing_azure_values_in_prompt.missing = missing_values

        return {
            'execution_state': execution_state,
            'messages': [response]
        }
    

    def check_with_human_on_missing_values(self, execution_state: ExecutionState) -> dict:

        missing_values = execution_state.scratchpad.missing_azure_values_in_prompt.missing

        if not missing_values:
            return {}


        guide_user_to_fill_values = f'please provide the missing values for these fields separated by commas: {", ".join(missing_values.keys())}'
    

        # human-in-the-loop to fill in missing values
        filled_values = interrupt({'value_resolver_agent_missing_values': guide_user_to_fill_values})

        if filled_values:
            execution_state.scratchpad.missing_azure_values_in_prompt.filled = filled_values.split(',')

        return { 'execution_state': execution_state }
    

    def update_prompt_with_filled_values(self, execution_state: ExecutionState) -> dict:

        class RefinedPromptOutput(BaseModel):
            resolved_prompt: str = Field(default="", description="The enriched user prompt with filled Azure resource values")
        
        llm : AzureChatOpenAI= Util.gpt_4o()
        llm.with_structured_output(RefinedPromptOutput)

        user_prompt = execution_state.scratchpad.original_prompt
        missing_values = execution_state.scratchpad.missing_azure_values_in_prompt.missing
        filled_values = execution_state.scratchpad.missing_azure_values_in_prompt.filled

        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=update_user_prompt_with_filled_values_system_prompt.format(
                        user_prompt=user_prompt,
                        missing_values=missing_values,
                        filled_values=filled_values
                    )
                ),
                HumanMessage(content="update original prompt using the previously missing Azure values and filled Azure values.")
            ]
        ) | llm


        output: RefinedPromptOutput = messages.invoke({})
        resolved_prompt = output.resolved_prompt

        execution_state.scratchpad.resolved_prompt = resolved_prompt

        return {
            'execution_state': execution_state,
            'messages': [AIMessage(content=resolved_prompt)]
        }
    
    
    # conditional routing methods
    def need_human_to_fill_missing_values(self, execution_state: ExecutionState) -> str:
        if not execution_state.scratchpad.missing_azure_values_in_prompt.missing:
            return 'no_need_human_to_fill_missing_values'
        return 'need_human_to_fill_missing_values'



    def are_azure_missings_resolved(self, execution_state: ExecutionState) -> bool:
        missing_values = execution_state.scratchpad.missing_azure_values_in_prompt.missing
        filled_values = execution_state.scratchpad.missing_azure_values_in_prompt.filled    

        if not missing_values:
            return True
        
        if len(missing_values) != len(filled_values):
            return False
        
        return True



# if __name__ == "__main__":
#     from state import ExecutionState, Scratchpad
#     import asyncio
#     from dotenv import load_dotenv
#     load_dotenv()

#     state = ExecutionState(
#         scratchpad=Scratchpad(user_prompt="Create a new virtual machine in my resource group. VM size you decide for me.")
#     )
    
#     agent = ResolveValuesAgent()

#     result = asyncio.run(agent.prompt_human_for_missing_info(state))

#     print(result)

