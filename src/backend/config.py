from pathlib import Path

class Config:

    def __init__(self):
        self.cwd_dir = './.agent_cwd'
        self.ensure_cwd_exists()
        self.cwd = Path("./.agent_cwd").absolute()

    
    def ensure_cwd_exists(self):
        path = Path(self.cwd_dir)
        path.mkdir(parents=True, exist_ok=True)
