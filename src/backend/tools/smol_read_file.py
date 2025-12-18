from smolagents import Tool
from pydantic import BaseModel, Field
import os

class ReadFileOutput(BaseModel):
    success: bool = Field(..., description="Indicates if the file was read successfully")
    content: str = Field('', description="Content of the read file")
    error: str = Field('', description="Error message if the file read failed")

class SmolReadFileTool(Tool):
    name = "read_file_from_local_file_system"
    description = """
    Use this tool when you want to: read text content, code, or data from a file
    
    Important limitations:
    - Processes ONE file at a time only
    - Cannot perform batch operations on multiple files
    
    
    """

    inputs = {
        "file_path": {
            "type": "string",
            "description": "The path of the file to read (e.g., 'output.txt' or '/path/to/file.json')",
        }
    }
    output_schema = ReadFileOutput


    def forward(self, file_path: str, content: str):
        try:
            import os
            from pathlib import Path

            content = ''
            # Read content from the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return ReadFileOutput(success=True, content=content, error='')
        except Exception as e:
            return ReadFileOutput(success=False, content='', error=str(e))