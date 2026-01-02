from langchain_openai import AzureChatOpenAI
from state import ExecutionState
from utils import Util
from state import Task
from agents.prompt import task_planner_system_prompt
from agents.tools.az_cli import AzCliTool, AzureCliToolInput, AzCliToolCodeResult
from agents.tools.bash import BashTool, BashToolInput, BashToolCodeResult
from agents.tools.code import CodeTool
from agents.state import (ExecutionState,
                          TaskPlannerOutput, TaskPlan, Task,
                          AzCliToolCodeResult,
                          BashToolCodeResult)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import Any, Dict
import asyncio

class TaskPlanner:
    
    def plan_tasks(self, execution_state: ExecutionState) -> Dict[str, Any]:
        llm : AzureChatOpenAI = Util.gpt_4o()
        llm = llm.with_structured_output(TaskPlannerOutput)
        
        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=task_planner_system_prompt),
                HumanMessage(content=execution_state.scratchpad.original_prompt)
            ]   
        )

        chain = messages | llm

        task_planner_tasks: TaskPlannerOutput = chain.invoke({})

        task_plan = self._create_task_plan_from_output(task_planner_tasks)

        asyncio.run(self._generate_az_cli_bash_commands_from_prompt(task_plan))

        execution_state.scratchpad.task_plan = task_plan

        return {
            'execution_state': execution_state,
            'messages': [AIMessage(content=task_plan.model_dump_json(indent=2))]
        }
    

    def _create_task_plan_from_output(self, task_planner_output: TaskPlannerOutput) -> TaskPlan:
        task_plan = TaskPlan()
        for task_output in task_planner_output.tasks:
            task = Task(
                task_id=task_output.task_id,
                description=task_output.description,
                task_type=task_output.task_type,
                prompt=task_output.prompt
            )
            task_plan.tasks.append(task)
        return task_plan
    

    async def _generate_az_cli_bash_commands_from_prompt(self, task_plan: TaskPlan) -> str:
        
        for task in task_plan.tasks:  
            
            # "az_cli" | "python", "deep_research", "bash"

            if task.task_type == 'az_cli':
                az_cli_tool = AzCliTool()
                result: AzCliToolCodeResult = await az_cli_tool.arun({'prompt': task.prompt})
                task.az_cli_commands = result.commands

            elif task.task_type == 'bash':
                bash_tool = BashTool()
                result: BashToolCodeResult = await bash_tool.arun({'prompt': task.prompt})
                task.bash_commands = result.commands