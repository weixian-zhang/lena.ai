from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json
from agents.workflow import AzureWorkflow
from agents.state import ExecutionState, Scratchpad
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()


@app.get("/workflow/{thread_id}/stream")
async def stream_workflow(thread_id: str):
    async def event_generator():
        config = workflows[thread_id]["config"]
        
        # Stream workflow events
        for event in graph.stream(None, config, stream_mode="values"):
            yield f"data: {json.dumps(event)}\n\n"
            
            if event.get("status") == "waiting_for_input":
                yield f"event: interrupt\ndata: {json.dumps(event)}\n\n"
                break
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Client with SSE
# import sseclient
# import requests

# response = requests.get(f"{BASE_URL}/workflow/{workflow_id}/stream", stream=True)
# client = sseclient.SSEClient(response)

# for event in client.events():
#     if event.event == "interrupt":
#         # Handle interrupt immediately
#         user_input = collect_input(json.loads(event.data))
#         requests.post(f"{BASE_URL}/workflow/{workflow_id}/resume", 
#                      json={"user_input": user_input})



workflow = AzureWorkflow()
graph = workflow.build_graph()

prompt_1 = "Create an Azure VM with 4 CPUs and 16GB RAM in East US region."

config = {"configurable": {"thread_id": '1'}}

state = ExecutionState(
        scratchpad = Scratchpad(
            original_prompt = prompt_1
        )
    )

from typing import Tuple
from langgraph.types import interrupt, Command
def is_hitl_needed(result: dict) -> Tuple[bool, dict[str,str]]:
    interrupt = result.get('__interrupt__', False)
    interrupt_key = 'value_resolver_agent_missing_values'

    if not interrupt or interrupt_key not in interrupt[0].value:
        return False, ''
    
    missing_values_prompt = interrupt[0].value[interrupt_key]

    return True, missing_values_prompt


# stream event to client with SSE.  
# from fastapi.responses import StreamingResponse
# import asyncio

# @app.get("/workflow/{workflow_id}/stream")
# async def stream_workflow(workflow_id: str):
#     async def event_generator():
#         config = workflows[workflow_id]["config"]
        
#         # Stream workflow events
#         for event in graph.stream(None, config, stream_mode="values"):
#             yield f"data: {json.dumps(event)}\n\n"
            
#             if event.get("status") == "waiting_for_input":
#                 yield f"event: interrupt\ndata: {json.dumps(event)}\n\n"
#                 break
        
#         yield "data: [DONE]\n\n"
    
#     return StreamingResponse(event_generator(), media_type="text/event-stream")

# # Client with SSE
# import sseclient
# import requests

# response = requests.get(f"{BASE_URL}/workflow/{workflow_id}/stream", stream=True)
# client = sseclient.SSEClient(response)

# for event in client.events():
#     if event.event == "interrupt":
#         # Handle interrupt immediately
#         user_input = collect_input(json.loads(event.data))
#         requests.post(f"{BASE_URL}/workflow/{workflow_id}/resume", 
#                      json={"user_input": user_input})


while True:

    current_input = state

    # when interrupt() on server-side, this loop will break
    for event in graph.stream(input=state, config=config, stream_mode="values"):
        data = event #f"data: {json.dumps(event)}\n\n"

    # Check if interrupted
    state_snapshot = graph.get_state(config)
    
    if not state.next:
        # Completed
        print("Workflow completed!")
        break
        
    yes, missing_values = is_hitl_needed(event)
    if yes:
        filled_values = missing_values.copy()

        for k, v in missing_values.items():
            k_input = input(f"Please provide value for '{k}': ")
            filled_values[k] = k_input

        current_input = Command(resume=filled_values, update=state)

        
