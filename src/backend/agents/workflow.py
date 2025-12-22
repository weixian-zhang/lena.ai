from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from state import ExecutionState
from value_resolver_agent import ValueResolverAgent

class AzureWorkflow:
    """Workflow orchestrator"""
    
    def __init__(self):
        self.state: ExecutionState = ExecutionState()
        self.value_resolver_agent = ValueResolverAgent()
        self.workflow = StateGraph(ExecutionState)
    
    def _build_graph(self):

        self.workflow = StateGraph(ExecutionState)
        self.workflow.add_node("check_for_missing_azure_values", self.value_resolver_agent.check_for_missing_azure_values)
        self.workflow.add_node("check_with_human_on_missing_values", self.value_resolver_agent.check_with_human_on_missing_values)
        
        self.workflow.add_edge(START, "check_for_missing_azure_values")
        self.workflow.add_conditional_edges(
            "check_for_missing_azure_values", self.value_resolver_agent.need_human_fill_missing_values, 
            {
                "need_human_fill_missing_values": self.value_resolver_agent.check_with_human_on_missing_values, 
                "no_need_human_fill_missing_values": END
             }
        )
        return self.workflow.compile()
    

    def execute(self, user_prompt: str) -> dict:

        self.state.scratchpad.user_prompt = user_prompt
        return self.workflow.invoke(self.state)