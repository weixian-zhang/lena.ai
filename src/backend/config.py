from pathlib import Path
import os
class Config:

    def __init__(self):
        current_dir  = os.path.dirname(os.path.abspath(__file__))
        self.agent_cwd = os.path.join(current_dir, '.agent_cwd')
        self.ensure_cwd_exists(self.agent_cwd)

    
    def ensure_cwd_exists(self, path: str = None):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
