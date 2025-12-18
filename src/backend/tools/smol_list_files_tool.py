from smolagents import Tool
from pydantic import BaseModel, Field
import os

class ListFilesOutput(BaseModel):
    success: bool = Field(..., description="Indicates if the files were listed successfully")
    files: list = Field([], description="List of files in the directory")
    error: str = Field('', description="Error message if the file listing failed")

class SmolListFilesTool(Tool):
    name = "list_files_tool"
    description = """
    Use this tool when you want to: list files and subdirectories in a directory
    
    Important limitations:
    - can recursively list files and subdirectories only ONE level deep
    - Cannot perform batch operations on multiple directories
    
    Use this tool when you need to:
    - Explore directory contents
    - Verify file existence
    - Gather file metadata
    """

    inputs = {
        "file_path": {
            "type": "string",
            "description": "The path of the file to read (e.g., 'output.txt' or '/path/to/file.json')",
        }
    }
    output_schema = ListFilesOutput


    def forward(self, file_path: str, content: str):
        try:
            import os
            from pathlib import Path

            content = ''
            # Read content from the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return ListFilesOutput(success=True, files=content, error='')
        except Exception as e:
            return ListFilesOutput(success=False, files=[], error=str(e))