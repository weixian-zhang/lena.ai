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

        assert os.getenv("AGENT_WORKING_DIRECTORY") is not None, "AGENT_WORKING_DIRECTORY is not set in environment variables."
        assert os.getenv("AZURE_CLIENT_ID") is not None, "AZURE_CLIENT_ID is not set in environment variables."
        assert os.getenv("AZURE_CLIENT_SECRET") is not None, "AZURE_CLIENT_SECRET is not set in environment variables."
        assert os.getenv("AZURE_TENANT_ID") is not None, "AZURE_TENANT_ID is not set in environment variables."
        assert os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") is not None, "AZURE_OPENAI_DEPLOYMENT_NAME is not set in environment variables."
        assert os.getenv("AZURE_OPENAI_MODEL_NAME") is not None, "AZURE_OPENAI_MODEL_NAME is not set in environment variables."
        assert os.getenv("AZURE_OPENAI_ENDPOINT") is not None, "AZURE_OPENAI_ENDPOINT is not set in environment variables."
        assert os.getenv("FOUNDRY_ENDPOINT") is not None, "FOUNDRY_ENDPOINT is not set in environment variables."
        assert os.getenv("AZURE_OPENAI_API_VERSION") is not None, "AZURE_OPENAI_API_VERSION is not set in environment variables."

        self.agent_cwd = os.getenv("AGENT_WORKING_DIRECTORY")
        self.ensure_cwd_exists(self.agent_cwd)
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.azure_openai_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.azure_openai_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.foundry_endpoint = os.getenv("FOUNDRY_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    
    def ensure_cwd_exists(self, path: str = None):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
