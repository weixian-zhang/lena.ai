import asyncio
from asyncio.subprocess import Process
from typing import Optional, Tuple
from click import command
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()


class AzShellResult(BaseModel):
    success: bool = Field(description="Indicates whether the command executed successfully.")
    stdout: Optional[str] = Field(description="The output of the executed shell command.")
    err_while_get_stdout: Optional[str] = Field(default=None, description="Error message if there was an error getting stdout.")
    stderr: Optional[str] = Field(default=None, description="The error output of the executed shell command.")
    err_while_get_stderr: Optional[str] = Field(default=None, description="Error message if there was an error getting stderr.")


class AzShell:
    """
    A class to execute shell commands either synchronously.
    """

    def __init__(self):
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

    # def _load_service_principal_credentials(self):
    #     """
    #     Load service principal credentials from environment variables.
    #     """
    #     import os

    #     self.client_id = os.getenv("AZURE_CLIENT_ID")
    #     self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
    #     self.tenant_id = os.getenv("AZURE_TENANT_ID")
    #     self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")


    async def _read_stream(stream):
        lines = []
        while True:
            line = await stream.readline()
            if line:
                lines.append(line.decode().strip())
            else:
                break

    async def _get_stdout_stderr(self, process: Process, timeout: float) -> Tuple[bool, str, str]:
        """
        Helper function to read stdout and stderr with timeout.
        
        returns: is_success, stdout_str, stderr_str
        """

        stdout = []
        err_while_get_stdout = ''
        
        while True:

            # if asyncio.get_event_loop().time() - start_time > timeout:
            #         raise asyncio.TimeoutError(f"Command timed out: {command}")
            
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=timeout)
                if not line:  # EOF
                    break

                line_str = line.decode().strip()
                stdout.append(line_str)
            except asyncio.TimeoutError:
                break
            except Exception as e:
                err_while_get_stdout = str(e)
                break


        stderr = []
        err_while_get_stderr = ''
        
        while True:
            try:
                line = await asyncio.wait_for(process.stderr.readline(), timeout=timeout)
                line_str = line.decode().strip()
                stderr.append(line_str)
                #line = await asyncio.wait_for(process.stderr.readline(), timeout=timeout)
            except asyncio.TimeoutError:
                break
            except Exception as e:
                err_while_get_stdout = str(e)
                break


        success = True if not stderr else False
        stdout = '\n'.join(stdout)
        stderr = '\n'.join(stderr)

        return success, stdout, err_while_get_stdout, stderr, err_while_get_stderr


    async def run(self, command: str, timeout: Optional[float] = 10) -> str:
        """
        Execute a command synchronously and return the output as a string.
        Waits for the command to complete before returning.
        
        Args:
            command: The shell command to execute
            timeout: Optional timeout in seconds (raises TimeoutError if exceeded)
        
        Returns:
            Command output as string (stdout). If there's stderr, it's included.
        
        Raises:
            TimeoutError: If command exceeds timeout
            RuntimeError: If command returns non-zero exit code
        """
        # Start an interactive bash shell
        process = await asyncio.create_subprocess_shell(
            "bash",  # or "zsh", "sh", etc.
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # process = subprocess.Popen(
        #     ['bash'], # Use 'cmd.exe' on Windows
        #     stdin=subprocess.PIPE,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     text=True, # For Python 3, handle as text
        #     shell=False # We are managing the shell ourselves
        # )

        try:
            # stdout, stderr = await asyncio.wait_for(
            #     process.communicate(),
            #     timeout=timeout
            # )

            # Azure authn with service principal
            az_login = f"az login --service-principal -u {self.client_id} -p {self.client_secret} --tenant {self.tenant_id}"

            # process.stdin.write(az_login)
            # process.stdin.flush() # Ensure the command is sent immediately
            # # stdout, stderr = process.communicate()
            
            # stdout, stderr = [], []
            # for line in process.stdout:
            #     stdout.append(line.decode().strip())

            # for line in process.stderr:
            #     stderr.append(line.decode().strip())

            process.stdin.write(f"{az_login}\n".encode())
            await process.stdin.drain()

            success, stdout, err_while_get_stdout, stderr, err_while_get_stderr = await self._get_stdout_stderr(process, timeout)

            if stderr:
                return AzShellResult(
                    success=False,
                    stdout=stdout,
                    stderr=stderr
                )
            
            process.stdin.write(f"{command}\n".encode())
            await process.stdin.drain()
             # Send the actual command
            # process.stdin.write(f"{command}\n".encode())
            # await process.stdin.drain()

            success, stdout, err_while_get_stdout, stderr, err_while_get_stderr = await self._get_stdout_stderr(process, timeout)

            shell_result = AzShellResult(
                success=success,
                stdout=stdout,
                err_while_get_stdout=err_while_get_stdout,
                stderr=stderr,
                err_while_get_stderr=err_while_get_stderr
            )

            return shell_result


            # # Decode output
            # stdout_str = stdout.decode() if stdout else ""
            # stderr_str = stderr.decode() if stderr else ""

            # shell_result = ShellResult(
            #     success=(process.returncode == 0),
            #     output=stdout_str,
            #     error=stderr_str if process.returncode != 0 else None
            # )


        except Exception as e:
            return AzShellResult(
                    success=False,
                    stdout='',
                    stderr=str(e)
                )
        finally:
            process.kill()
            await process.wait()
    



    # async def run_command_background(self, command: str) -> asyncio.subprocess.Process:
    #     """
    #     Run a command asynchronously in the background without blocking.
    #     Returns immediately with the process object.
    #     """
    #     process = await asyncio.create_subprocess_shell(
    #         command,
    #         stdout=asyncio.subprocess.PIPE,
    #         stderr=asyncio.subprocess.PIPE
    #     )
    #     print(f"Started background process with PID: {process.pid}")
    #     return process

