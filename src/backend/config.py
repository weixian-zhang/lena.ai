from pathlib import Path
import os

    # singleton implementation
class Config:

    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Config, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True

        self.agent_cwd = os.getenv("AGENT_WORKING_DIRECTORY")
        self.ensure_cwd_exists(self.agent_cwd)
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.azure_openai_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.azure_openai_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    
    def ensure_cwd_exists(self, path: str = None):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
