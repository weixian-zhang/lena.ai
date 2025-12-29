from langchain_openai import AzureChatOpenAI
from state import ExecutionState
from utils import Util
from agents.prompt import task_planner_system_prompt
from agents.state import ExecutionState,  TaskPlan
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import Any, Dict

class TaskPlanner:
    
    def plan_tasks(self, execution_state: ExecutionState) -> Dict[str, Any]:
        llm : AzureChatOpenAI = Util.gpt_4o()
        llm = llm.with_structured_output(TaskPlan)
        
        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=task_planner_system_prompt),
                HumanMessage(content=execution_state.scratchpad.original_prompt)
            ]   
        )

        chain = messages | llm

        task_plan: TaskPlan = chain.invoke({})

        prompts = [t.tool.prompt for t in task_plan.tasks]

        return task_plan
    

    def execute_tool(self, execution_state: ExecutionState) -> str:
        pass