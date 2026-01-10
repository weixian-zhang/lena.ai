from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph, StateT, ContextT, InputT, OutputT
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from utils import Util
from datetime import datetime
from agents.state import ExecutionState, Scratchpad
from agents.task_planner_agent import TaskPlanner
from agents.task_runner_agent import TaskRunner
# from agents.task_param_collector_agent import ValueResolverAgent
from typing import Tuple

class AzureWorkflow:
    """Workflow orchestrator"""
    
    def __init__(self):
        self.state: ExecutionState = ExecutionState()
        self.task_planner = TaskPlanner()
        self.task_runner = TaskRunner()
    

    def build_graph(self) -> CompiledStateGraph[StateT, ContextT, InputT, OutputT]:

        checkpointer = InMemorySaver()

        self.workflow = StateGraph(ExecutionState)

        self.workflow.add_node("plan_tasks", self.task_planner.plan_tasks)
        self.workflow.add_node("optimize_prompt", self.task_planner.optimize_user_prompt)
        self.workflow.add_node("run_tasks", self.task_runner.run_tasks)

        self.workflow.add_edge(START, "optimize_prompt")
        self.workflow.add_edge("optimize_prompt", "plan_tasks")
        self.workflow.add_edge("plan_tasks", "run_tasks")
        self.workflow.add_edge("run_tasks", END)
        # self.workflow.add_node("check_for_missing_azure_values", self.value_resolver_agent.check_for_missing_azure_values)
        # self.workflow.add_node("check_with_human_on_missing_values", self.value_resolver_agent.check_with_human_on_missing_values)
        # self.workflow.add_node('update_prompt_with_filled_values', self.value_resolver_agent.update_prompt_with_filled_values)
        # self.workflow.add_edge(START, "check_for_missing_azure_values")
        # self.workflow.add_conditional_edges(
        #     "check_for_missing_azure_values", self.value_resolver_agent.need_human_to_fill_missing_values,
        #     {
        #         "need_human_to_fill_missing_values":  'check_with_human_on_missing_values', 
        #         "no_need_human_to_fill_missing_values": END
        #      }
        # )
        # # after human fills in missing values, re-check for missing values
        # self.workflow.add_edge("check_with_human_on_missing_values", 'update_prompt_with_filled_values')
        # self.workflow.add_edge('update_prompt_with_filled_values', 'check_for_missing_azure_values')
        self.workflow = self.workflow.compile(checkpointer=checkpointer)

        return self.workflow
    

    def invoke(self, user_prompt: str) -> dict:

        self.state.scratchpad.original_prompt = user_prompt
        return self.workflow.invoke(self.state)
    

    def is_missing_values_for_human_input(self, result: dict) -> Tuple[bool, dict[str,str]]:
        
        interrupt = result.get('__interrupt__', False)
        interrupt_key = 'value_resolver_agent_missing_values'

        if not interrupt or interrupt_key not in interrupt[0].value:
            return False, ''
        
        missing_values_prompt = interrupt[0].value[interrupt_key]

        return True, missing_values_prompt

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    from config import Config
    config = Config()

    

    workflow = AzureWorkflow()
    graph = workflow.build_graph()

    prompt_qa_1 = "What is Microsoft Azure?"
    prompt_1 = "Create an Azure VM with 4 CPUs and 16GB RAM in East US region."

    prompt_2 = """
    create a new resource group name rg-lena-test-1 in Southeast asia region.
    in the new resource group newly created, create 3 VNets named vnet-lena-1, vnet-lena-2, and vnet-lena-3, each VNet should have 1 subnet.
    the 1 subnet name in each Nvet should be subnet-lena-1, subnet-lena-2, and subnet-lena-3 respectively.
    peer the 3 VNets together.
    create total 3 VMs across the 3 VNets as below:
    create 1 Linux VM of size 'Standard_D4d_v5' named vm-linux-lena-1 in subnet-lena-1
    create 1 Linux VM of size 'Standard_D4d_v5' named vm-linux-lena-12 in subnet-lena-2
    create 1 Windows VM of size 'Standard_D4d_v5' named vm-windows-lena-1 in subnet-lena-3
    """

    prompt_app_1 = """
    1. create a 3.13 python Fast API app with single route /health returning "OK". Write a Docker file for it.
    2. create 
    1. The front-end should be hosted on Azure App Service.
    2. The back-end should be hosted on Azure Functions.
    3. The database should be an Azure SQL Database."""

    thread_id = "1"
    graph_config = {"configurable": {"thread_id": thread_id}} #str(uuid.uuid4())}}
    run_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
    username = 'admin@MngEnvMCAP049172.onmicrosoft.com'
    agent_working_dir = Util().set_agent_working_dir(config.agent_cwd, username, thread_id)

    state = ExecutionState(
        username = username,
        thread_id = thread_id,
        agent_working_directory = agent_working_dir,
        scratchpad = Scratchpad(
            original_prompt = prompt_2
        )
    )
    
    result = graph.invoke(input=state, config=graph_config)

    pass
    # yes, missing_values = workflow.is_missing_values_for_human_input(result)
    # if yes:

    #     filled_values = missing_values.copy()

    #     for k, v in missing_values.items():
    #         k_input = input(f"Please provide value for '{k}': ")
    #         filled_values[k] = k_input

    #     state.scratchpad.missing_azure_values_in_prompt.filled = filled_values
        
    #     result = graph.invoke(Command(resume=filled_values, update=state), config=config)

    #     print(result)
    # else:
    #     print("Final Result:", result)