from pydantic import BaseModel, Field

class Config(BaseModel):
    agent_working_directory: str = Field(
        default="./.agent_cwd",
        description="The working directory for the agent to store temporary files and data."
    )