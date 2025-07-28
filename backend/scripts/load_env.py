"""Load environment variables from .env file."""

import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file."""
    # Try to find .env file
    current_dir = Path(__file__).parent
    env_paths = [
        current_dir / '..' / '.env',  # backend/.env
        current_dir / '..' / '..' / '.env',  # project root
        current_dir / '.env'  # scripts/.env
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            print(f"Loading environment from: {env_path.resolve()}")
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"').strip("'")
                        os.environ[key] = value
            return True
    
    return False