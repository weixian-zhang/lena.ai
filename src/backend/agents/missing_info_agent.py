from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.checkpoint.memory import InMemorySaver


# check for missing Azure info critical for Azure select, create or update Azure operations.
# subscription id, resource group, location, name of resource.
# example: tasks could be data engineering related like download file from Azure Storage, Storage name, resource group and subscription id to find the Storage is critical.
