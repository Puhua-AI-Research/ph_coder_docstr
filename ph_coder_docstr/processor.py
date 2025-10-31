"""
Main processor module for handling file traversal and comment generation.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from .config import Config, SUPPORTED_EXTENSIONS
from .parser import CodeParser, CodeUnit
from .api_client import APIClient


class DocumentationProcessor:
    """Main processor for adding documentation to code files."""
    
    def __init__(self, project_path: str, config: Config):
        """
        Initialize the processor.
        
        Args:
            project_path: Path to the project directory
            config: Configuration object
        """
        self.project_path = Path(project_path).resolve()
        self.config = config
        self.api_client = APIClient(config)
        self.progress_file = self.project_path / ".ph_coder_docstr_progress.json"
        self.completed_files = self._load_progress()
    
    def _load_progress(self) -> Dict[str, bool]:
        """Load progress from JSON file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load progress file: {e}")
        return {}
    
    def _save_progress(self):
        """Save progress to JSON file."""
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(self.completed_files, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save progress file: {e}")
    
    def find_code_files(self) -> List[Path]:
        """
        Find all supported code files in the project.
        
        Returns:
            List of file paths
        """
        code_files = []
        
        for ext in SUPPORTED_EXTENSIONS.keys():
            # Find all files with this extension
            files = self.project_path.rglob(f"*{ext}")
            for file in files:
                # Skip hidden directories and common ignore patterns
                parts = file.relative_to(self.project_path).parts
                if any(part.startswith(".") or part in ["node_modules", "__pycache__", "venv", "env", "build", "dist"] for part in parts):
                    continue
                code_files.append(file)
        
        return sorted(code_files)
    
    def process_file(self, file_path: Path) -> bool:
        """
        Process a single file to add documentation.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        # Check if already completed
        relative_path = str(file_path.relative_to(self.project_path))
        if relative_path in self.completed_files:
            print(f"Skipping {relative_path} (already completed)")
            return True
        
        print(f"\nProcessing: {relative_path}")
        
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Determine language
            ext = file_path.suffix
            language = SUPPORTED_EXTENSIONS.get(ext, "unknown")
            
            if language == "unknown":
                print(f"  Skipping unsupported file type: {ext}")
                return False
            
            # Parse the file
            parser = CodeParser(language)
            units = parser.split_into_units(content)
            
            print(f"  Found {len(units)} code units")
            
            # Generate comments for each unit
            commented_units = []
            for i, unit in enumerate(units):
                print(f"  Processing unit {i + 1}/{len(units)}...", end=" ")
                
                # Skip very small units (less than 3 lines)
                if unit.get_line_count() < 3:
                    print("skipped (too small)")
                    commented_units.append(unit)
                    continue
                
                # Generate comment
                comment = self.api_client.generate_comment(
                    unit.content,
                    language,
                    unit.unit_type
                )
                
                if comment:
                    # Use no indentation - comments are always at column 0 (顶格)
                    unit.comment = self.api_client.format_comment(comment, language, "")
                    print("✓")
                else:
                    print("✗ (failed)")
                
                commented_units.append(unit)
            
            # Generate file-level comment
            print("  Generating file-level comment...", end=" ")
            file_comment = self.api_client.generate_comment(
                content,
                language,
                "file"
            )
            
            if file_comment:
                # File-level comment also uses no indentation (顶格)
                file_comment = self.api_client.format_comment(file_comment, language, "")
                print("✓")
            else:
                file_comment = ""
                print("✗ (failed)")
            
            # Reconstruct the file with comments
            new_content = self._reconstruct_file(content, commented_units, file_comment)
            
            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Write the new content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Mark as completed
            self.completed_files[relative_path] = True
            self._save_progress()
            
            print(f"  ✓ Successfully processed {relative_path}")
            return True
            
        except Exception as e:
            print(f"  ✗ Error processing {relative_path}: {e}")
            return False
    
    def _has_actual_code(self, content: str) -> bool:
        """
        Check if content has actual code (not just whitespace or empty).
        
        Args:
            content: Code content to check
            
        Returns:
            True if has actual code, False otherwise
        """
        # Check if content is empty or only whitespace
        stripped = content.strip()
        return len(stripped) > 0
    
    def _reconstruct_file(self, original_content: str, units: List[CodeUnit], file_comment: str) -> str:
        """
        Reconstruct file content with comments added before code.
        Comments are only added for code units that have actual content.
        
        Args:
            original_content: Original file content
            units: List of code units with comments
            file_comment: File-level comment
            
        Returns:
            New file content with comments
        """
        lines = original_content.split("\n")
        new_lines = []
        
        # Add file-level comment at the beginning (only if there's actual code in the file)
        if file_comment and original_content.strip():
            new_lines.extend(file_comment.split("\n"))
            new_lines.append("")
        
        # Track which lines we've processed
        processed_lines = set()
        
        # Sort units by start line
        units.sort(key=lambda u: u.start_line)
        
        current_line = 0
        for unit in units:
            # Add any lines before this unit
            while current_line < unit.start_line:
                if current_line not in processed_lines:
                    new_lines.append(lines[current_line])
                    processed_lines.add(current_line)
                current_line += 1
            
            # Check if this unit has actual code content
            unit_content = "\n".join(lines[unit.start_line:min(unit.end_line + 1, len(lines))])
            has_code = self._has_actual_code(unit_content)
            
            # Add the unit's content first (only if it has actual code)
            if has_code:
                for i in range(unit.start_line, min(unit.end_line + 1, len(lines))):
                    if i not in processed_lines:
                        new_lines.append(lines[i])
                        processed_lines.add(i)
                
                # Add comment AFTER code (only if unit has actual code and comment exists)
                if unit.comment:
                    new_lines.extend(unit.comment.split("\n"))
            else:
                # Mark lines as processed even if we skip them
                for i in range(unit.start_line, min(unit.end_line + 1, len(lines))):
                    processed_lines.add(i)
            
            current_line = unit.end_line + 1
        
        # Add any remaining lines
        while current_line < len(lines):
            if current_line not in processed_lines:
                new_lines.append(lines[current_line])
            current_line += 1
        
        return "\n".join(new_lines)
    
    def process_project(self):
        """Process all files in the project."""
        if not self.project_path.exists():
            print(f"Error: Project path does not exist: {self.project_path}")
            return
        
        if not self.project_path.is_dir():
            print(f"Error: Project path is not a directory: {self.project_path}")
            return
        
        print(f"Processing project: {self.project_path}")
        print(f"Using API base URL: {self.config.base_url}")
        print(f"Using models: {', '.join(self.config.models_list)}")
        
        # Find all code files
        code_files = self.find_code_files()
        print(f"\nFound {len(code_files)} code files")
        
        if not code_files:
            print("No code files found to process")
            return
        
        # Process each file
        successful = 0
        failed = 0
        
        for file_path in code_files:
            if self.process_file(file_path):
                successful += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "=" * 50)
        print("Processing complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Progress saved to: {self.progress_file}")
        print("=" * 50)

