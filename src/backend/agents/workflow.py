from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph, StateT, ContextT, InputT, OutputT
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage
from state import ExecutionState, Scratchpad
from value_resolver_agent import ValueResolverAgent
from typing import Tuple

class AzureWorkflow:
    """Workflow orchestrator"""
    
    def __init__(self):
        self.state: ExecutionState = ExecutionState()
        self.value_resolver_agent = ValueResolverAgent()
        self.workflow = CompiledStateGraph[StateT, ContextT, InputT, OutputT]
    
    def build_graph(self) -> CompiledStateGraph[StateT, ContextT, InputT, OutputT]:

        checkpointer = InMemorySaver()

        self.workflow = StateGraph(ExecutionState)
        self.workflow.add_node("check_for_missing_azure_values", self.value_resolver_agent.check_for_missing_azure_values)
        self.workflow.add_node("check_with_human_on_missing_values", self.value_resolver_agent.check_with_human_on_missing_values)
        
        self.workflow.add_edge(START, "check_for_missing_azure_values")
        self.workflow.add_conditional_edges(
            "check_for_missing_azure_values", self.value_resolver_agent.need_human_to_fill_missing_values,
            {
                "need_human_to_fill_missing_values":  'check_with_human_on_missing_values', 
                "no_need_human_to_fill_missing_values": END
             }
        )
        # after human fills in missing values, re-check for missing values
        self.workflow.add_edge("check_with_human_on_missing_values", 'check_for_missing_azure_values')
        self.workflow = self.workflow.compile(checkpointer=checkpointer)

        return self.workflow
    

    def invoke(self, user_prompt: str) -> dict:

        self.state.scratchpad.original_prompt = user_prompt
        return self.workflow.invoke(self.state)
    

    def is_missing_values_for_human_input(self, result: dict) -> Tuple[bool, str]:
        
        interrupt = result.get('__interrupt__', False)
        interrupt_key = 'value_resolver_agent_missing_values'

        if not interrupt or interrupt_key not in interrupt[0].value:
            return False, ''
        
        missing_values_prompt = interrupt[0].value[interrupt_key]

        return True, missing_values_prompt

if __name__ == "__main__":
    from state import Agents
    from dotenv import load_dotenv
    load_dotenv()

    config = {"configurable": {"thread_id": '1'}} #str(uuid.uuid4())}}

    workflow = AzureWorkflow()
    graph = workflow.build_graph()

    state = ExecutionState(
        scratchpad = Scratchpad(
            original_prompt = "Create an Azure VM with 4 CPUs and 16GB RAM in East US region."
        )
    )
    
    result = graph.invoke(input=state, config=config)

    yes, missing_values_prompt = workflow.is_missing_values_for_human_input(result)
    if yes:
        filled_values = input(missing_values_prompt)
        
        result = graph.invoke(Command(resume=filled_values), config=config)

        print(result)
    else:
        print("Final Result:", result)