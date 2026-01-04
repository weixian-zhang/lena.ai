from langchain_openai import AzureChatOpenAI
from state import ExecutionState, Task
from tools.az_shell import AzShell
from tools.code import CodeTool
from tools.deep_research import DeepResearchTool
from state import (AzCliTaskCommandParameterResult, BashTaskCommandParameterResult, 
                   AzShellToolExecutionResult, DeepResearchToolExecutionResult, CodeToolExecutionResult)
from state import TaskType, AzCliTask, BashTask, PythonTask, DeepResearchTask
import asyncio

class TaskRunner:
    
    def run_tasks(self, execution_state: ExecutionState) -> None:

        for task in execution_state.scratchpad.task_plan.tasks:
            
            if task.task_type == 'az_cli':
                asyncio.run(self._run_az_cli_task(task))

            elif task.task_type == 'python':
                asyncio.run(self._run_python_task(task))

            elif task.task_type == 'deep_research':
                asyncio.run(self._run_deep_research_task(task))

            elif task.task_type == 'bash':
                asyncio.run(self._run_bash_task(task))
        
        return {
            'scratchpad': execution_state.scratchpad,
            'messages': []
        }
    

    async def _run_az_cli_task(self, task: AzCliTask) -> Task:
        shell = AzShell()

        for tpc in task.commands:
            result: AzShellToolExecutionResult = await shell.arun(tpc.command)
            tpc.execution_result = result


    async def _run_bash_task(self, task: BashTask) -> Task:
        shell = AzShell()

        for tpc in task.commands:
            result: AzShellToolExecutionResult = await shell.arun(tpc.command)
            tpc.execution_result = result

    async def _run_python_task(self, task: PythonTask) -> Task:
        code_tool = CodeTool()

        result: CodeToolExecutionResult = await code_tool.arun(task.prompt)
        task.execution_result = result

    async def _run_deep_research_task(self, task: DeepResearchTask) -> Task:
        research_tool = DeepResearchTool()

        result: DeepResearchToolExecutionResult = await research_tool.arun(task.prompt)
        task.execution_result = result

        