"""
Code parser module for extracting functions from different programming languages.
"""

import re
from typing import List, Tuple, Dict
from .config import MAX_LINES_PER_UNIT


class CodeUnit:
    """Represents a unit of code (function, class, or chunk)."""
    
    def __init__(self, content: str, start_line: int, end_line: int, unit_type: str = "chunk"):
        """
        Initialize a code unit.
        
        Args:
            content: The code content
            start_line: Starting line number (0-indexed)
            end_line: Ending line number (0-indexed)
            unit_type: Type of unit (function, class, chunk)
        """
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.unit_type = unit_type
        self.comment = ""
    
    def get_line_count(self) -> int:
        """Get the number of lines in this unit."""
        return len(self.content.split("\n"))


class CodeParser:
    """Parser for extracting code units from source files."""
    
    # Function detection patterns for different languages
    FUNCTION_PATTERNS = {
        "python": [
            r"^(\s*)(def\s+\w+\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:)",
            r"^(\s*)(class\s+\w+(?:\([^)]*\))?\s*:)",
            r"^(\s*)(@\w+(?:\([^)]*\))?)\s*$",  # decorators
        ],
        "javascript": [
            r"^(\s*)(function\s+\w+\s*\([^)]*\)\s*\{)",
            r"^(\s*)((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function\s*\([^)]*\)\s*\{)",
            r"^(\s*)((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{)",
            r"^(\s*)(class\s+\w+(?:\s+extends\s+\w+)?\s*\{)",
        ],
        "typescript": [
            r"^(\s*)(function\s+\w+\s*\([^)]*\)\s*:\s*\w+\s*\{)",
            r"^(\s*)((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function\s*\([^)]*\)(?:\s*:\s*\w+)?\s*\{)",
            r"^(\s*)((?:const|let|var)\s+\w+\s*:\s*\([^)]*\)\s*=>\s*\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{)",
            r"^(\s*)(class\s+\w+(?:\s+extends\s+\w+)?(?:\s+implements\s+\w+)?\s*\{)",
        ],
        "c": [
            r"^(\s*)(\w+\s+\w+\s*\([^)]*\)\s*\{)",
            r"^(\s*)(struct\s+\w+\s*\{)",
        ],
        "cpp": [
            r"^(\s*)(\w+(?:::\w+)*\s+\w+\s*\([^)]*\)(?:\s+const)?\s*\{)",
            r"^(\s*)(class\s+\w+(?:\s*:\s*(?:public|private|protected)\s+\w+)?\s*\{)",
            r"^(\s*)(struct\s+\w+\s*\{)",
            r"^(\s*)(namespace\s+\w+\s*\{)",
        ],
        "cuda": [
            r"^(\s*)(__global__|__device__|__host__)\s+\w+\s+\w+\s*\([^)]*\)\s*\{",
            r"^(\s*)(\w+\s+\w+\s*\([^)]*\)\s*\{)",
        ],
        "go": [
            r"^(\s*)(func\s+(?:\([^)]*\)\s*)?\w+\s*\([^)]*\)(?:\s*\([^)]*\))?\s*\{)",
            r"^(\s*)(type\s+\w+\s+struct\s*\{)",
            r"^(\s*)(type\s+\w+\s+interface\s*\{)",
        ],
    }
    
    def __init__(self, language: str):
        """
        Initialize the parser for a specific language.
        
        Args:
            language: Programming language type
        """
        self.language = language
        self.patterns = self.FUNCTION_PATTERNS.get(language, [])
    
    def find_function_starts(self, lines: List[str]) -> List[int]:
        """
        Find line numbers where functions start.
        
        Args:
            lines: List of code lines
            
        Returns:
            List of line indices where functions start
        """
        function_starts = []
        
        for i, line in enumerate(lines):
            for pattern in self.patterns:
                if re.match(pattern, line):
                    function_starts.append(i)
                    break
        
        return function_starts
    
    def find_block_end(self, lines: List[str], start: int) -> int:
        """
        Find the end of a code block by tracking braces/indentation.
        
        Args:
            lines: List of code lines
            start: Starting line index
            
        Returns:
            Ending line index
        """
        if self.language == "python":
            return self._find_python_block_end(lines, start)
        else:
            return self._find_brace_block_end(lines, start)
    
    def _find_python_block_end(self, lines: List[str], start: int) -> int:
        """Find the end of a Python block using indentation."""
        if start >= len(lines):
            return len(lines) - 1
        
        # Get the indentation level of the starting line
        start_line = lines[start]
        base_indent = len(start_line) - len(start_line.lstrip())
        
        # Find the end of the block
        for i in range(start + 1, len(lines)):
            line = lines[i]
            if line.strip() == "":
                continue
            
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent:
                return i - 1
        
        return len(lines) - 1
    
    def _find_brace_block_end(self, lines: List[str], start: int) -> int:
        """Find the end of a block using brace matching."""
        if start >= len(lines):
            return len(lines) - 1
        
        brace_count = 0
        started = False
        
        for i in range(start, len(lines)):
            line = lines[i]
            for char in line:
                if char == '{':
                    brace_count += 1
                    started = True
                elif char == '}':
                    brace_count -= 1
                    if started and brace_count == 0:
                        return i
        
        return len(lines) - 1
    
    def split_into_units(self, content: str) -> List[CodeUnit]:
        """
        Split code content into units (functions or chunks).
        
        Args:
            content: Full file content
            
        Returns:
            List of CodeUnit objects
        """
        lines = content.split("\n")
        units = []
        
        # Find all function starts
        function_starts = self.find_function_starts(lines)
        
        if not function_starts:
            # No functions found, split by chunks
            return self._split_by_chunks(lines)
        
        # Process each function
        processed_lines = set()
        for start in function_starts:
            end = self.find_block_end(lines, start)
            
            # Mark these lines as processed
            for i in range(start, end + 1):
                processed_lines.add(i)
            
            function_content = "\n".join(lines[start:end + 1])
            unit = CodeUnit(function_content, start, end, "function")
            
            # If the function is too long, split it further
            if unit.get_line_count() > MAX_LINES_PER_UNIT:
                sub_units = self._split_long_unit(unit)
                units.extend(sub_units)
            else:
                units.append(unit)
        
        # Handle any remaining unprocessed lines
        current_chunk = []
        chunk_start = 0
        for i, line in enumerate(lines):
            if i not in processed_lines:
                if not current_chunk:
                    chunk_start = i
                current_chunk.append(line)
                
                if len(current_chunk) >= MAX_LINES_PER_UNIT:
                    chunk_content = "\n".join(current_chunk)
                    if chunk_content.strip():
                        units.append(CodeUnit(chunk_content, chunk_start, i, "chunk"))
                    current_chunk = []
            else:
                if current_chunk:
                    chunk_content = "\n".join(current_chunk)
                    if chunk_content.strip():
                        units.append(CodeUnit(chunk_content, chunk_start, i - 1, "chunk"))
                    current_chunk = []
        
        # Add any remaining chunk
        if current_chunk:
            chunk_content = "\n".join(current_chunk)
            if chunk_content.strip():
                units.append(CodeUnit(chunk_content, chunk_start, len(lines) - 1, "chunk"))
        
        # Sort units by start line
        units.sort(key=lambda u: u.start_line)
        
        return units
    
    def _split_by_chunks(self, lines: List[str]) -> List[CodeUnit]:
        """Split code into chunks when no functions are found."""
        units = []
        for i in range(0, len(lines), MAX_LINES_PER_UNIT):
            chunk = lines[i:i + MAX_LINES_PER_UNIT]
            content = "\n".join(chunk)
            if content.strip():
                units.append(CodeUnit(content, i, min(i + len(chunk) - 1, len(lines) - 1), "chunk"))
        return units
    
    def _split_long_unit(self, unit: CodeUnit) -> List[CodeUnit]:
        """Split a long code unit into smaller chunks."""
        lines = unit.content.split("\n")
        sub_units = []
        
        for i in range(0, len(lines), MAX_LINES_PER_UNIT):
            chunk = lines[i:i + MAX_LINES_PER_UNIT]
            content = "\n".join(chunk)
            if content.strip():
                start = unit.start_line + i
                end = unit.start_line + min(i + len(chunk) - 1, len(lines) - 1)
                sub_units.append(CodeUnit(content, start, end, "chunk"))
        
        return sub_units

