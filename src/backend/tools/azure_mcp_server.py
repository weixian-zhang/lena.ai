import asyncio

class AzureMCPServer:
    def __init__(self):
        pass

    async def run(cmd):
        proc = await asyncio.create_subprocess_shell(
            "npx -y @azure/mcp@latest server start", 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return stdout, stderr, proc.returncode

