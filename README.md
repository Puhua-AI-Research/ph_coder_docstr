# ph_coder_docstr

A tool to automatically add documentation comments to code files using AI.

## Features

- 🌍 **Multi-language support**: Python, C/C++, CUDA, JavaScript, TypeScript, Go
- 🤖 **AI-powered**: Uses OpenAI-compatible APIs to generate meaningful comments
- 🔄 **Smart retry**: Automatic retry with exponential backoff
- 🔁 **Model rotation**: Round-robin through multiple models to avoid rate limits
- 📊 **Progress tracking**: Resume processing after interruptions
- 💾 **Safe**: Creates backups before modifying files
- ⚡ **Intelligent splitting**: Splits large functions into manageable chunks

## Installation

### From Wheel

```bash
pip install ph_coder_docstr-0.1.0-py3-none-any.whl
```

### From Source

```bash
cd /workspace/code/ph_coder_docstr
pip install -e .
```

## Configuration

Set up environment variables in a `.env` file or export them:

```bash
export OPENAI_API_KEY=your_api_key
export OPENAI_URL=https://api.openai.com/v1
export OPENAI_MODELS_LIST=gpt-4o-mini,gpt-4o
```

Or create a `.env` file:

```
OPENAI_API_KEY=your_api_key
OPENAI_URL=https://api.openai.com/v1
OPENAI_MODELS_LIST=gpt-4o-mini,gpt-4o
```

## Usage

### Command Line

```bash
python3 -m ph_coder_docstr --project ./path/to/your/project
```

Or if installed as a package:

```bash
ph_coder_docstr --project ./path/to/your/project
```

### Example

```bash
# Set up environment
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_URL=https://ph8.co
export OPENAI_MODELS_LIST=gpt-4o-mini,gpt-4o

# Process a project
python3 -m ph_coder_docstr --project /workspace/code/tmp
```

## How It Works

1. **File Discovery**: Scans the project directory for supported code files
2. **Code Parsing**: Identifies functions, classes, and code blocks
3. **Smart Splitting**: Breaks down large functions (>50 lines) into chunks
4. **Comment Generation**: Uses AI to generate meaningful comments for each unit
5. **File Documentation**: Creates a file-level overview comment
6. **Safe Writing**: Creates backups and writes commented code
7. **Progress Tracking**: Saves progress to avoid reprocessing on retry

## Supported File Types

- Python (`.py`)
- C (`.c`)
- C++ (`.cpp`)
- CUDA (`.cu`, `.cuh`)
- JavaScript (`.js`, `.jsx`)
- TypeScript (`.ts`, `.tsx`)
- Go (`.go`)

## Features

### Intelligent Code Analysis

The tool recognizes:
- Function definitions
- Class declarations
- Decorators (Python)
- Type annotations
- Block structures

### Comment Style

Comments are formatted according to language conventions:
- **Python**: Docstrings (`"""..."""`)
- **C/C++/CUDA**: C-style comments (`/* ... */` or `// ...`)
- **JavaScript/TypeScript**: JSDoc-style comments
- **Go**: Go-style comments

### Progress Tracking

A `.ph_coder_docstr_progress.json` file is created in the project root to track completed files. This allows you to:
- Resume processing after interruption
- Skip already processed files
- Avoid wasting API credits on reprocessing

### Retry Mechanism

- Automatic retry on API failures (up to 3 attempts)
- Exponential backoff between retries
- Model rotation to avoid rate limits

## Requirements

- Python 3.8+
- openai >= 1.0.0
- python-dotenv >= 1.0.0

## Development

### Project Structure

```
ph_coder_docstr/
├── setup.py
├── requirements.txt
├── README.md
└── ph_coder_docstr/
    ├── __init__.py
    ├── __main__.py      # CLI entry point
    ├── config.py        # Configuration management
    ├── parser.py        # Code parsing logic
    ├── api_client.py    # API communication
    └── processor.py     # Main processing logic
```

### Building Wheel

```bash
pip install build
python -m build
```

## License

MIT

## Author

PH Coder
