from langchain_openai import AzureChatOpenAI
from state import ExecutionState, Task
from tools.az_cli import AzCliToolResult 


class TaskExecutionOverseer:
    
    def run(self, execution_state: ExecutionState) -> None:


        for task in execution_state.scratchpad.task_plan.tasks:
            
            # "az_cli" | "python", "deep_research", "bash"

            if task.task_type == 'az_cli':
                # execute az cli command
                pass
            elif task.task_type == 'python':
                # execute python code
                pass
            elif task.task_type == 'deep_research':
                # perform deep research
                pass
            elif task.task_type == 'bash':
                # execute bash command
                pass
        
        return {
            'scratchpad': execution_state.scratchpad,
            'messages': []
        }
    
    def _run_az_cli_task(self, task: Task) -> Task:
        az_cli_tool = task.tool

        