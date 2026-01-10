from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel
from state import ExecutionState
from utils import Util
from state import TaskType, AzCliTask, BashTask, PythonTask, DeepResearchTask
from agents.prompt import task_planner_system_prompt, task_planner_prompt_optimizer
from agents.tools.az_cli import AzCliTool, AzCliToolCodeResult
from agents.tools.bash import BashTool, BashToolCodeResult
from agents.state import (ExecutionState,
                          TaskPlannerOutput, TaskPlan, AzCliTaskCommandParameterResult, BashTaskCommandParameterResult,
                          AzCliToolCodeResult,
                          BashToolCodeResult)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import Any, Dict
import asyncio


class UserPromptOptimizerStructuredOutput(BaseModel):
    optimized_prompt: str


class TaskPlanner:
    
    def plan_tasks(self, execution_state: ExecutionState) -> Dict[str, Any]:

        assert execution_state.scratchpad.optimized_prompt is not None, "Optimized prompt is required"
        
        scratchpad = execution_state.scratchpad
        
        llm : AzureChatOpenAI = Util.gpt_4o()
        llm = llm.with_structured_output(TaskPlannerOutput)
        
        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=task_planner_system_prompt),
                HumanMessage(content=execution_state.scratchpad.optimized_prompt)
            ]   
        )

        chain = messages | llm

        task_planner_tasks: TaskPlannerOutput = chain.invoke({})

        task_plan = self._create_task_plan_from_output(task_planner_tasks)

        asyncio.run(self._generate_az_cli_bash_commands_from_prompt(task_plan))

        scratchpad.task_plan = task_plan

        return {
            'scratchpad': scratchpad
            # 'messages': [AIMessage(content=task_plan.model_dump_json(indent=2))]
        }
    
    
    def optimize_user_prompt(self, execution_state: ExecutionState) -> str:
        llm : AzureChatOpenAI = Util.gpt_4o()
        llm = llm.with_structured_output(UserPromptOptimizerStructuredOutput)

        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=task_planner_prompt_optimizer),
                HumanMessage(content=execution_state.scratchpad.original_prompt)
            ]   
        )

        chain = messages | llm

        output: UserPromptOptimizerStructuredOutput = chain.invoke({})

        optimized_prompt = output.optimized_prompt

        execution_state.scratchpad.optimized_prompt = optimized_prompt

        return {
            'execution_state': execution_state,
            'messages': [AIMessage(content='optimized_prompt: ' + optimized_prompt)]
        }
    

    def _create_task_plan_from_output(self, task_planner_output: TaskPlannerOutput) -> TaskPlan:
        task_plan = TaskPlan()
        for planner_task in task_planner_output.tasks:
            
            task = None

            if planner_task.task_type == TaskType.AZ_CLI:
                task = AzCliTask(
                    task_id=planner_task.task_id,
                    description=planner_task.description,
                    task_type=planner_task.task_type,
                    prompt=planner_task.prompt
                )
            elif planner_task.task_type == TaskType.BASH:
                task = BashTask(
                    task_id=planner_task.task_id,
                    description=planner_task.description,
                    task_type=planner_task.task_type,
                    prompt=planner_task.prompt
                )
            elif planner_task.task_type == TaskType.PYTHON:
                task = PythonTask(
                    task_id=planner_task.task_id,
                    description=planner_task.description,
                    task_type=planner_task.task_type,
                    prompt=planner_task.prompt
                )
            elif planner_task.task_type == TaskType.DEEP_RESEARCH:
                task = DeepResearchTask(
                    task_id=planner_task.task_id,
                    description=planner_task.description,
                    task_type=planner_task.task_type,
                    prompt=planner_task.prompt
                )
            task_plan.tasks.append(task)

        return task_plan
    

    async def _generate_az_cli_bash_commands_from_prompt(self, task_plan: TaskPlan) -> str:
        i = 0
        for task in task_plan.tasks:  

            if i == 1:
                break
            i += 1

            if task.task_type == 'az_cli':
                az_cli_tool = AzCliTool()
                result: AzCliToolCodeResult = await az_cli_tool.arun({'prompt': task.prompt})
                for command in result.commands:
                    task.commands.append(AzCliTaskCommandParameterResult(
                        command=command
                    ))

            elif task.task_type == 'bash':
                bash_tool = BashTool()
                result: BashToolCodeResult = await bash_tool.arun({'prompt': task.prompt})
                for command in result.commands:
                    task.commands.append(BashTaskCommandParameterResult(
                        command=command
                    ))