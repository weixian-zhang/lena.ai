from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph, StateT, ContextT, InputT, OutputT
from langchain_core.messages import HumanMessage
from state import ExecutionState
from value_resolver_agent import ValueResolverAgent

class AzureWorkflow:
    """Workflow orchestrator"""
    
    def __init__(self):
        self.state: ExecutionState = ExecutionState()
        self.value_resolver_agent = ValueResolverAgent()
        self.workflow = CompiledStateGraph[StateT, ContextT, InputT, OutputT]
    
    def _build_graph(self):

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
        self.workflow = self.workflow.compile()
    

    def invoke(self, user_prompt: str) -> dict:

        self.state.scratchpad.original_prompt = user_prompt
        return self.workflow.invoke(self.state)
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    azure_workflow = AzureWorkflow()
    azure_workflow._build_graph()
    result = azure_workflow.invoke("Create an Azure VM with 4 CPUs and 16GB RAM in East US region.")
    print("Final Result:", result)