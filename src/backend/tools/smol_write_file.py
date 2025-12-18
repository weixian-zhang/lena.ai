from smolagents import Tool
from pydantic import BaseModel, Field
import os

class WriteFileOutput(BaseModel):
    success: bool = Field(..., description="Indicates if the file was written successfully")
    error: str = Field('', description="Error message if the file write failed")

class SmolWriteFileTool(Tool):
    name = "write_file_tool"
    description = """
    Use this tool when you want to: Write content to a file on the local file system. Creates a new file or overwrites an existing file.
    
    Important limitations:
    - Processes ONE file at a time only
    - Cannot perform batch operations on multiple files
    
    Use this tool when you need to:
    - Save text content, code, or data to a file
    - Create configuration files
    - Export results or reports"""
    inputs = {
        "file_path": {
            "type": "string",
            "description": "The path where the file should be written (e.g., 'output.txt' or '/path/to/file.json')",
        },
        "content": {
            "type": "string",
            "description": "The text content to write to the file",
        }
    }
    output_schema = WriteFileOutput


    def forward(self, file_path: str, content: str):
        try:
            import os
            from pathlib import Path

            # Write content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return WriteFileOutput(success=True, error='')
        except Exception as e:
            return WriteFileOutput(success=False, error=str(e))