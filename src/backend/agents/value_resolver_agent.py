from langgraph.types import interrupt, Command
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from prompt import missing_info_system_prompt
from state import ExecutionState
from utils import Util
import json


class ResolveValuesAgentOutput(BaseModel):
    required_values: dict[str, str] = Field(default={}, description="A dictionary containing the missing information for human to fill in")


class ValueResolverAgent:

    def check_for_missing_azure_values(self, execution_state: ExecutionState) -> dict:

        llm: AzureChatOpenAI = Util.gpt_4o()

        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=missing_info_system_prompt),
                HumanMessage(content=execution_state.scratchpad.user_prompt)
            ]   
        )

        missing_info_chain = chat_template | llm

        filled_missing_values = execution_state.scratchpad.filled_missing_values

        response = missing_info_chain.invoke(input={"filled_missing_values": filled_missing_values})

        if response.content.strip() != "{}":
            missing_values: dict[str, str] = json.loads(response.content.strip())
            execution_state.scratchpad.prompt_azure_missing_values.missing_values = missing_values

        return {
            'execution_state': execution_state,
            'messages': [response]
        }
    

    def check_with_human_on_missing_values(self, execution_state: ExecutionState) -> dict:

        missing_values = execution_state.scratchpad.prompt_azure_missing_values.missing_values

        if not missing_values:
            return {}


        guide_user_to_fill_values = f'please provide the missing values for these fields separated by commas: {", ".join(missing_values.keys())}'
        
        # human-in-the-loop to fill in missing values
        filled_values = interrupt(guide_user_to_fill_values)

        if filled_values:
            execution_state.scratchpad.prompt_azure_missing_values.filled_values = filled_values.split(',')

        return { 'execution_state': execution_state }
    
    
    # conditional routing methods
    def need_human_fill_missing_values(self, execution_state: ExecutionState) -> str:
        missing_values = execution_state.scratchpad.prompt_azure_missing_values.missing_values
        if not missing_values:
            return 'no_need_human_fill_missing_values'
        return 'need_human_fill_missing_values'

    def are_azure_missings_resolved(self, execution_state: ExecutionState) -> bool:
        missing_values = execution_state.scratchpad.prompt_azure_missing_values.missing_values
        filled_values = execution_state.scratchpad.prompt_azure_missing_values.filled_values

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

