import asyncio
from asyncio.subprocess import Process
from typing import Optional, Tuple
from click import command
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from langchain_core.tools import BaseTool
from typing import Type

import sys
import subprocess

load_dotenv()

class AzShellToolInput(BaseModel):
    command: str = Field(description="The bash or Azure CLI command to execute.")

class AzShellToolResult(BaseModel):
    success: bool = Field(description="Indicates whether the command executed successfully.")
    stdout: Optional[str] = Field(description="The output of the executed shell command.")
    stderr: Optional[str] = Field(default=None, description="The error output of the executed shell command.")

# class AzShellToolResult(BaseModel):
#     success: bool = Field(description="Indicates whether the command executed successfully.")
#     stdout: Optional[str] = Field(description="The output of the executed shell command.")
#     err_while_get_stdout: Optional[str] = Field(default=None, description="Error message if there was an error getting stdout.")
#     stderr: Optional[str] = Field(default=None, description="The error output of the executed shell command.")
#     err_while_get_stderr: Optional[str] = Field(default=None, description="Error message if there was an error getting stderr.")


class AzShell(BaseTool):
    name: str = "azure_bash_shell"
    description: str = """
    Executes bash and Azure CLI commands in a pre-authenticated Azure shell.

    Run any bash command, execute az CLI commands, perform file operations, chain commands with pipes.

    Use this tool to directly execute commands on Azure cloud or local system. No authentication needed - shell is already logged into Azure.
    """
    args_schema: Type[BaseModel] = AzShellToolInput
    response_format: Type[BaseModel] = AzShellToolResult

    # def __init__(self):
    #     self.client_id = os.getenv("AZURE_CLIENT_ID")
    #     self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
    #     self.tenant_id = os.getenv("AZURE_TENANT_ID")
    #     self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")


    # async def _read_stream(stream):
    #     lines = []
    #     while True:
    #         line = await stream.readline()
    #         if line:
    #             lines.append(line.decode().strip())
    #         else:
    #             break


    def _run(self, prompt: str) -> str:
        """Generate code snippet from the given prompt."""
        raise NotImplementedError("Synchronous code generation is not implemented.")


    async def _arun(self, command: str, timeout: Optional[int] = 1) -> str:
        """Asynchronously generate Azure CLI command from the given prompt."""
        """
        Execute a command synchronously and return the output as a string.
        Waits for the command to complete before returning.
        
        Args:
            command: The shell command to execute
            timeout: Optional timeout in seconds  default 5 (raises TimeoutError if exceeded)
        
        Returns:
            Command output as string (stdout). If there's stderr, it's included.
        
        Raises:
            TimeoutError: If command exceeds timeout
            RuntimeError: If command returns non-zero exit code
        """
        

        try:

            
            
            # Azure authn with service principal
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            tenant_id = os.getenv("AZURE_TENANT_ID")
            # subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
            az_login = f"az login --service-principal -u {client_id} -p {client_secret} --tenant {tenant_id}"


            # Start an interactive bash shell
            # process = subprocess.Popen(
            #     az_login + ';' + command,
            #     shell=True,
            #     executable='/bin/bash',
            #     stdout=subprocess.PIPE,
            #     stderr=subprocess.PIPE,
            #     text=True
            # )
            
            # stdout, stderr = process.communicate(timeout=60)

            import pexpect
            child = pexpect.spawn('bash') 

            
    
            # Optional: Log the output to stdout for debugging
            child.logfile = sys.stdout.buffer

            prompt = r'\$' 

            child.sendline(az_login + '; echo __LOGIN_DONE__')

            child.expect('__LOGIN_DONE__')


            # --- Run Command 1: Change directory (cd) ---
            # 'cd' doesn't usually produce output, but we still expect the next prompt
            child.sendline(command + '; echo __CMD_DONE__')

            child.expect('__CMD_DONE__')

            before = child.before

            pass
            
            

            # import subprocess
            # ret = subprocess.run(az_login + ';' + command, capture_output=True, shell=True)

            # stdout = ret.stdout.decode()
            # stderr = ret.stderr.decode()
            # success = ret.returncode == 0

            # process.stdin.write(f"{az_login}\n".encode())
            # await process.stdin.drain()

            # # success, stdout, err_while_get_stdout, stderr, err_while_get_stderr = await self._get_stdout_stderr(process, timeout)
            # success, stdout, stderr = await self._get_stdout_stderr(process, timeout)

            # if stderr:
            #     return AzShellToolResult(
            #         success=False,
            #         stdout=stdout,
            #         stderr=stderr
            #     )
            
            # process.stdin.write(f"{command}\n".encode())
            # await process.stdin.drain()


            # # success, stdout, err_while_get_stdout, stderr, err_while_get_stderr = await self._get_stdout_stderr(process, timeout)
            # success, stdout, stderr = await self._get_stdout_stderr(process, timeout)

            shell_result = AzShellToolResult(
                success=True if not stderr else False,
                stdout=stdout,
                stderr=stderr
            )

            return shell_result


        except Exception as e:
            return AzShellToolResult(
                    success=False,
                    stdout='',
                    stderr=str(e)
                )



    async def _get_stdout_stderr(self, process: Process, timeout: float) -> Tuple[bool, str, str]:
        """
        Helper function to read stdout and stderr with timeout.
        
        returns: is_success, stdout_str, stderr_str
        """

        stdout = []
        max_line = 100
        current_line = 0

        while True:

            if current_line >= max_line:
                break

            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=timeout)
                if not line:  # EOF
                    break

                line_str = line.decode().strip()
                stdout.append(line_str)

                current_line += 1
            except asyncio.TimeoutError:
                break


        stderr = []
        is_warning = False
        current_line = 0
        
        while True:
            if current_line >= max_line:
                break

            try:
                line = await asyncio.wait_for(process.stderr.readline(), timeout=timeout)
                line_str = line.decode().strip()
                if not is_warning and '[Warning]' in line.decode():
                    is_warning = True
                stderr.append(line_str)

                current_line += 1
            except asyncio.TimeoutError:
                break


        success = True if not stderr else False
        stdout = '\n'.join(stdout)
        stderr = '\n'.join(stderr)


        return success, stdout, stderr


if __name__ == "__main__":
    import asyncio

    az_shell = AzShell()

    async def test_az_shell():
        #command = "az account list  -o tsv"
        command = "az vm list-skus --location southeastasia --output table"
        result = await az_shell.ainvoke(command, timeout=5)
        print("Success:", result.success)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    asyncio.run(test_az_shell())
