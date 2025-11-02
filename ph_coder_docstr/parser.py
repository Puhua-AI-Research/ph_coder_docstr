"""
Code parser module for extracting functions from different programming languages.
"""

import re
from typing import List, Tuple, Dict
from .config import MAX_LINES_PER_UNIT


class CodeUnit:
    """Represents a unit of code (function, class, or chunk)."""
    
    def __init__(self, content: str, start_line: int, end_line: int, unit_type: str = "chunk", section: str = None):
        """
        Initialize a code unit.
        
        Args:
            content: The code content
            start_line: Starting line number (0-indexed)
            end_line: Ending line number (0-indexed)
            unit_type: Type of unit (function, class, chunk)
            section: Section type for Vue files (template, script, style)
        """
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.unit_type = unit_type
        self.section = section  # For Vue files: template, script, or style
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
            r"^(\s*)((?:async\s+)?function\s+\w+\s*\([^)]*\)\s*\{)",  # function (including async)
            r"^(\s*)((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function\s*\([^)]*\)\s*\{)",  # function expression
            r"^(\s*)((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{)",  # arrow function
            r"^(\s*)(class\s+\w+(?:\s+extends\s+\w+)?\s*\{)",  # class
            r"^(\s*)(\w+\s*\([^)]*\)\s*\{)",  # method definition (e.g., add(a, b) {)
        ],
        "typescript": [
            r"^(\s*)((?:async\s+)?function\s+\w+\s*\([^)]*\)(?:\s*:\s*[\w\[\]<>]+)?\s*\{)",  # function with optional return type
            r"^(\s*)((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function\s*\([^)]*\)(?:\s*:\s*[\w\[\]<>]+)?\s*\{)",  # function expression
            r"^(\s*)((?:const|let|var)\s+\w+\s*:\s*\([^)]*\)\s*=>\s*[\w\[\]<>]+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{)",  # complex arrow
            r"^(\s*)(class\s+\w+(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w\s,]+)?\s*\{)",  # class
            r"^(\s*)(interface\s+\w+(?:\s+extends\s+[\w\s,]+)?\s*\{)",  # interface
            r"^(\s*)(\w+\s*\([^)]*\)(?:\s*:\s*[\w\[\]<>]+)?\s*\{)",  # method definition
        ],
        "c": [
            r"^(\s*)((?:[\w\*]+\s+)+\w+\s*\([^)]*\)\s*\{)",  # function (including pointer types like void*)
            r"^(\s*)(struct\s+\w+\s*\{)",  # struct
        ],
        "cpp": [
            r"^(\s*)((?:virtual\s+)?(?:[\w\*]+(?:::\w+)*\s+)*\w+(?:::\w+)+\s*\([^)]*\)(?:\s+const)?\s*\{)",  # method/constructor with ::
            r"^(\s*)((?:virtual\s+)?(?:[\w\*]+(?:::\w+)*\s+)+\w+\s*\([^)]*\)(?:\s+const)?\s*\{)",  # function with return type
            r"^(\s*)(class\s+\w+(?:\s*:\s*(?:public|private|protected)\s+\w+)?\s*\{)",  # class
            r"^(\s*)(struct\s+\w+\s*\{)",  # struct
            r"^(\s*)(namespace\s+\w+\s*\{)",  # namespace
        ],
        "cuda": [
            r"^(\s*)((?:__global__|__device__|__host__)\s+[\w\*]+\s+\w+\s*\([^)]*\)\s*\{)",  # CUDA kernel
            r"^(\s*)((?:[\w\*]+\s+)+\w+\s*\([^)]*\)\s*\{)",  # regular function
        ],
        "go": [
            r"^(\s*)(func\s+(?:\([^)]*\)\s*)?\w+\s*\([^)]*\)(?:\s+[\w\[\]\*\.]+)?(?:\s*\([^)]*\))?\s*\{)",  # function with optional single or multiple return values
            r"^(\s*)(type\s+\w+\s+struct\s*\{)",  # struct
            r"^(\s*)(type\s+\w+\s+interface\s*\{)",  # interface
        ],
        "vue": [
            # Vue uses JavaScript/TypeScript in <script> section
            r"^(\s*)((?:async\s+)?function\s+\w+\s*\([^)]*\)\s*\{)",  # function (including async)
            r"^(\s*)((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function\s*\([^)]*\)\s*\{)",  # function expression
            r"^(\s*)((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{)",  # arrow function
            r"^(\s*)(export\s+default\s+\{)",  # export default (Vue component)
            r"^(\s*)(data\s*\(\s*\)\s*\{)",  # data function
            r"^(\s*)(computed\s*:\s*\{)",  # computed properties
            r"^(\s*)(methods\s*:\s*\{)",  # methods
            r"^(\s*)(mounted\s*\(\s*\)\s*\{)",  # lifecycle hooks
            r"^(\s*)(created\s*\(\s*\)\s*\{)",  # lifecycle hooks
            r"^(\s*)(\w+\s*\([^)]*\)\s*\{)",  # method definition
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
        # Special handling for Vue files
        if self.language == "vue":
            return self._split_vue_file(content)
        
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
    
    def _split_vue_file(self, content: str) -> List[CodeUnit]:
        """
        Split Vue single-file component into sections and units.
        
        Args:
            content: Full Vue file content
            
        Returns:
            List of CodeUnit objects with section information
        """
        lines = content.split("\n")
        units = []
        
        # Find Vue sections
        sections = self._find_vue_sections(lines)
        
        for section_type, start_line, end_line in sections:
            section_content = "\n".join(lines[start_line:end_line + 1])
            
            # Create a temporary parser for the section's language
            if section_type == "script":
                section_parser = CodeParser("javascript")
            elif section_type == "style":
                # For style, we'll just create chunks
                section_parser = None
            else:  # template
                # For template, we'll just create chunks
                section_parser = None
            
            if section_parser:
                # Parse the section as JavaScript
                section_units = section_parser.split_into_units(section_content)
                # Adjust line numbers and add section info
                for unit in section_units:
                    unit.start_line += start_line
                    unit.end_line += start_line
                    unit.section = section_type
                    units.append(unit)
            else:
                # Create a single unit for template or style sections
                unit = CodeUnit(section_content, start_line, end_line, "chunk", section=section_type)
                units.append(unit)
        
        return units
    
    def _find_vue_sections(self, lines: List[str]) -> List[Tuple[str, int, int]]:
        """
        Find template, script, and style sections in Vue file.
        
        Args:
            lines: List of file lines
            
        Returns:
            List of (section_type, start_line, end_line) tuples
            Note: Only includes content INSIDE the tags (excluding the tag lines themselves)
        """
        sections = []
        current_section = None
        section_start = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check for section start (opening tag)
            if stripped.startswith("<template"):
                current_section = "template"
                section_start = i + 1  # Start from the line after the opening tag
            elif stripped.startswith("<script"):
                current_section = "script"
                section_start = i + 1  # Start from the line after the opening tag
            elif stripped.startswith("<style"):
                current_section = "style"
                section_start = i + 1  # Start from the line after the opening tag
            # Check for section end (closing tag)
            elif stripped == "</template>" or stripped == "</script>" or stripped == "</style>":
                if current_section:
                    # Only add section if there's content between the tags
                    if i > section_start:
                        sections.append((current_section, section_start, i - 1))
                    current_section = None
        
        # Handle the last section if not closed
        if current_section and section_start < len(lines):
            sections.append((current_section, section_start, len(lines) - 1))
        
        return sections
    
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

