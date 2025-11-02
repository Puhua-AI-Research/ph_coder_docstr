"""
Configuration module for loading environment variables and settings.
"""

import os
from typing import List
from dotenv import load_dotenv


class Config:
    """Configuration class to manage environment variables and settings."""
    
    def __init__(self):
        """Initialize configuration by loading environment variables."""
        # Load .env file from project root
        load_dotenv()
        
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_URL", "https://api.openai.com/v1")
        models_str = os.getenv("OPENAI_MODELS_LIST", "gpt-4o-mini")
        self.models_list = [m.strip() for m in models_str.split(",") if m.strip()]
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        
        if not self.models_list:
            raise ValueError("OPENAI_MODELS_LIST is empty or invalid")
    
    def get_model(self, index: int = 0) -> str:
        """
        Get a model from the list using round-robin selection.
        
        Args:
            index: Index for round-robin selection
            
        Returns:
            Model name
        """
        return self.models_list[index % len(self.models_list)]


# Supported file extensions and their language types
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".cpp": "cpp",
    ".cc": "cpp",      # C++ alternative extension
    ".cxx": "cpp",     # C++ alternative extension
    ".c": "c",
    ".h": "c",         # C/C++ header file (default to C)
    ".hpp": "cpp",     # C++ header file
    ".hh": "cpp",      # C++ header file alternative
    ".cu": "cuda",
    ".cuh": "cuda",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".ts": "typescript",
    ".js": "javascript",
    ".vue": "vue",
    ".go": "go",
}

# Maximum lines for a single code unit before splitting
MAX_LINES_PER_UNIT = 50

