from langchain_openai import AzureChatOpenAI
from state import ExecutionState
from utils import Util
from prompt import task_planner_system_prompt

class TaskPlanner:
    
    def __init__(self, execution_state: ExecutionState):
        self.llm = Util.gpt_4o()
        self.execution_state = execution_state

    def plan_tasks(self, prompt: str) -> str:
        llm : AzureChatOpenAI= Util.gpt_4o()
        
        response = llm.predict(f"Create a detailed task plan to accomplish the following goal: {prompt}")
        return response