from langchain_openai import AzureChatOpenAI
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
from config import Config

class Util:

    @staticmethod
    def gpt_4o() -> str:
        config = Config()

        return AzureChatOpenAI(
                        deployment_name=config.azure_openai_deployment_name,
                        model=config.azure_openai_model_name,
                        api_version=config.azure_openai_api_version,
                        temperature=0.0
                    )
    
    @staticmethod
    def import_parent_dir_module(current_file_dunder: str):
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(current_file_dunder), '..'))
        sys.path.insert(0, parent_dir)