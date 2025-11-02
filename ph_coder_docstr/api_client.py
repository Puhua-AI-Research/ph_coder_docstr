"""
API client module for communicating with OpenAI-compatible APIs.
"""

import time
from typing import Optional
from openai import OpenAI
from .config import Config


class APIClient:
    """Client for making API calls to OpenAI-compatible services."""
    
    def __init__(self, config: Config):
        """
        Initialize the API client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        self.model_index = 0
    
    def generate_comment(
        self, 
        code: str, 
        language: str, 
        context: str = "function",
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate a comment for a code snippet.
        
        Args:
            code: The code to comment
            language: Programming language
            context: Context type (function, chunk, file)
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated comment or None if failed
        """
        # Define comment style requirements for each language
        comment_style_guide = {
            "python": "使用 # 符号开头的单行或多行注释",
            "javascript": "使用 // 或 /* */ 格式的注释",
            "typescript": "使用 // 或 /* */ 格式的注释",
            "vue": "使用 // 或 /* */ 格式的注释（Vue单文件组件）",
            "c": "使用 /* */ 或 // 格式的注释",
            "cpp": "使用 /* */ 或 // 格式的注释",
            "cuda": "使用 /* */ 或 // 格式的注释",
            "go": "使用 // 格式的注释",
        }
        
        style_guide = comment_style_guide.get(language, "使用该语言的标准注释格式")
        
        if context == "file":
            system_prompt = f"你是一个专业的代码注释助手，擅长为{language}代码编写规范的文档注释。"
            user_prompt = f"""请为这个{language}文件编写文件级注释说明。

要求：
1. {style_guide}
2. 每行注释不超过30个字符（中英文混合计算）
3. 使用多行注释，每行独立
4. 简洁清晰地说明文件的主要功能和用途
5. 不要包含代码，只返回注释文本
6. 不要使用markdown代码块格式

代码：
```{language}
{code}
```"""
        else:
            system_prompt = f"你是一个专业的代码注释助手，擅长为{language}代码编写规范的文档注释。"
            user_prompt = f"""请为这段{language}代码编写简洁的注释。

要求：
1. {style_guide}
2. 每行注释不超过30个字符（中英文混合计算）
3. 使用多行注释，每行独立
4. 简要说明代码的功能
5. 不要包含代码，只返回注释文本
6. 不要使用markdown代码块格式

代码：
```{language}
{code}
```"""
        
        for attempt in range(max_retries):
            try:
                # Get the current model using round-robin
                model = self.config.get_model(self.model_index)
                self.model_index += 1
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                comment = response.choices[0].message.content.strip()
                return comment
                
            except Exception as e:
                print(f"  Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    print(f"  Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed after {max_retries} attempts")
                    return None
        
        return None
    
    def _split_long_line(self, text: str, max_length: int = 30) -> list:
        """
        Split a long text into multiple lines with max length.
        
        Args:
            text: Text to split
            max_length: Maximum characters per line
            
        Returns:
            List of split lines
        """
        if len(text) <= max_length:
            return [text]
        
        lines = []
        current_line = ""
        
        # Split by existing newlines first
        for paragraph in text.split("\n"):
            words = paragraph.split()
            current_line = ""
            
            for word in words:
                # If adding this word would exceed limit
                if len(current_line) + len(word) + 1 > max_length:
                    if current_line:
                        lines.append(current_line.strip())
                        current_line = word
                    else:
                        # Single word is too long, split it
                        lines.append(word[:max_length])
                        current_line = word[max_length:]
                else:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
            
            if current_line:
                lines.append(current_line.strip())
        
        return lines if lines else [text]
    
    def format_comment(self, comment: str, language: str, indent: str = "") -> str:
        """
        Format a comment according to language conventions.
        
        Args:
            comment: The comment text
            language: Programming language
            indent: Indentation string
            
        Returns:
            Formatted comment
        """
        # Remove markdown code blocks if present
        if comment.startswith("```"):
            lines = comment.split("\n")
            # Remove first and last line if they're markdown markers
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            comment = "\n".join(lines).strip()
        
        # Clean up comment text
        comment = comment.strip()
        if not comment:
            return ""
        
        # Split comment into lines respecting existing line breaks
        raw_lines = comment.split("\n")
        processed_lines = []
        
        # Process each line to ensure max length
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove all common comment markers more thoroughly
            # Remove leading markers: //, /*, #, *
            while line and line[0] in ['/', '*', '#']:
                if line.startswith('//') or line.startswith('/*'):
                    line = line[2:].strip()
                elif line.startswith('#'):
                    line = line[1:].strip()
                elif line.startswith('*'):
                    line = line[1:].strip()
                else:
                    break
            
            # Remove trailing markers: */, */
            while line and len(line) >= 2:
                if line.endswith('*/'):
                    line = line[:-2].strip()
                elif line.endswith('*'):
                    line = line[:-1].strip()
                else:
                    break
            
            # Final strip
            line = line.strip()
            
            # Skip empty lines after cleaning
            if not line:
                continue
                
            # Split long lines
            split_lines = self._split_long_line(line, max_length=30)
            processed_lines.extend(split_lines)
        
        if not processed_lines:
            return ""
        
        # Format based on language
        if language == "python":
            # Python uses # for comments, not docstrings
            formatted_lines = [f'{indent}# {line}' for line in processed_lines]
            return "\n".join(formatted_lines)
        
        elif language in ["javascript", "typescript", "vue"]:
            # JavaScript/TypeScript/Vue prefer // for multi-line comments
            formatted_lines = [f'{indent}// {line}' for line in processed_lines]
            return "\n".join(formatted_lines)
        
        elif language == "go":
            # Go uses // for comments
            formatted_lines = [f'{indent}// {line}' for line in processed_lines]
            return "\n".join(formatted_lines)
        
        elif language in ["c", "cpp", "cuda"]:
            # C/C++/CUDA use /* */ for multi-line comments
            if len(processed_lines) == 1:
                return f'{indent}// {processed_lines[0]}'
            else:
                formatted = f'{indent}/*\n'
                for line in processed_lines:
                    formatted += f'{indent} * {line}\n'
                formatted += f'{indent} */'
                return formatted
        
        else:
            # Default to # style comments
            formatted_lines = [f'{indent}# {line}' for line in processed_lines]
            return "\n".join(formatted_lines)

