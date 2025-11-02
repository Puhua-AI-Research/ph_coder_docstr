# ph_coder_docstr

A tool to automatically add documentation comments to code files using AI.

## Features

- 🌍 **Multi-language support**: Python, C/C++, CUDA, JavaScript, TypeScript, Go (100% test coverage)
- 🤖 **AI-powered**: Uses OpenAI-compatible APIs to generate meaningful comments
- 🔄 **Smart retry**: Automatic retry with exponential backoff
- 🔁 **Model rotation**: Round-robin through multiple models to avoid rate limits
- 📊 **Progress tracking**: Resume processing after interruptions
- 💾 **Safe**: Creates backups before modifying files
- ⚡ **Intelligent splitting**: Splits large functions into manageable chunks
- ✨ **Enhanced pattern matching**: Recognizes async functions, constructors, interfaces, and more

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

#### Generate Documentation

```bash
python3 -m ph_coder_docstr --project ./path/to/your/project
```

Or if installed as a package:

```bash
ph_coder_docstr --project ./path/to/your/project
```

#### Clean Backup Files

After confirming the generated documentation is correct, you can clean up backup files:

```bash
# Dry run to see what would be deleted
python3 -m ph_coder_docstr --project ./path/to/your/project --clean-backups --dry-run

# Actually delete backup files (with confirmation prompt)
python3 -m ph_coder_docstr --project ./path/to/your/project --clean-backups
```

### Example

```bash
# Set up environment
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_URL=https://ph8.co
export OPENAI_MODELS_LIST=gpt-4o-mini,gpt-4o

# Process a project
python3 -m ph_coder_docstr --project /workspace/code/tmp

# After verifying the results, clean backup files
python3 -m ph_coder_docstr --project /workspace/code/tmp --clean-backups
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

### Complete Language Support (100% Pattern Coverage)

- **Python** (`.py`): Functions, classes, methods, decorators, type annotations
- **JavaScript** (`.js`, `.jsx`): Functions, async functions, arrow functions, classes, methods
- **TypeScript** (`.ts`, `.tsx`): All JS features + interfaces, type annotations
- **Go** (`.go`): Functions with single/multiple returns, methods with receivers, structs, interfaces
- **C** (`.c`): Functions with all return types (including pointers), structs
- **C++** (`.cpp`): Functions, methods, constructors, virtual functions, classes, namespaces
- **CUDA** (`.cu`, `.cuh`): Kernel functions, device functions, host functions

For detailed language support information, see [LANGUAGE_SUPPORT.md](LANGUAGE_SUPPORT.md).

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
- **Python**: `# Comments` (each line starts with #)
- **C/C++/CUDA**: `/* Multi-line */` or `// Single line`
- **JavaScript/TypeScript**: `// Comments` (each line starts with //)
- **Go**: `// Comments` (each line starts with //)

All comments are automatically line-wrapped to 30 characters per line for readability.

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
