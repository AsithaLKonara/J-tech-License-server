# Cloudie CLI Integration Guide

## Overview

This document describes the integration of Cloudie CLI (or similar AI CLI tools) for prompt-based LED matrix pattern generation in the Design Tools tab.

## Features

- **Prompt-based pattern generation**: Generate LED matrix patterns from natural language descriptions
- **Cloudie CLI integration**: Uses Cloudie CLI when available for advanced AI generation
- **Fallback generator**: Rule-based pattern generation when CLI is not available
- **Seamless integration**: Generated patterns load directly into the Design Tools editor

## Installation

### Option 1: Install Cloudie CLI (Recommended)

```bash
# Using npm (if Node.js is installed)
npm install -g @cloudie/cli

# Or using pip (if Python package exists)
pip install cloudie-cli

# Verify installation
cloudie --version
```

### Option 2: Use Fallback Generator

If Cloudie CLI is not installed, the system will automatically use a rule-based generator that creates patterns from common prompts like:
- "scrolling text"
- "bouncing ball"
- "rain effect"
- "fire effect"
- "gradient animation"

## Usage

### In the Design Tools Tab

1. Click the **"🤖 AI Generate"** button in the toolbar
2. Enter a prompt describing the pattern you want:
   - Examples:
     - "Scrolling text: Hello World"
     - "Bouncing ball animation"
     - "Fire effect"
     - "Rain animation"
     - "Gradient wave"
3. Configure settings:
   - Matrix size (width × height)
   - Number of frames
   - Animation style
   - Frame duration
4. Click **"Generate Pattern"**
5. The generated pattern will load automatically into the editor

### Example Prompts

**Text Animations:**
- "Scrolling text: Welcome"
- "Typing text: Hello"
- "Text scrolling left"

**Effects:**
- "Fire effect"
- "Rain animation"
- "Matrix rain"
- "Gradient wave"
- "Pulsing circle"

**Animations:**
- "Bouncing ball"
- "Rotating square"
- "Fading stars"
- "Moving dot"

## Architecture

### Components

1. **`core/ai_pattern_generator.py`**
   - `CloudieCLIInterface`: Interface to Cloudie CLI
   - `FallbackAIGenerator`: Rule-based pattern generator
   - `AIGenerationConfig`: Configuration dataclass

2. **`ui/dialogs/ai_generate_dialog.py`**
   - `AIGenerateDialog`: UI dialog for prompt input
   - `AIGenerationWorker`: Background thread for generation

3. **Integration in `ui/tabs/design_tools_tab.py`**
   - "🤖 AI Generate" button in toolbar
   - `_on_ai_generate_clicked()`: Handler for button click
   - `_on_ai_pattern_generated()`: Handler for generated pattern

### Workflow

```
User clicks "AI Generate" button
    ↓
AIGenerateDialog opens
    ↓
User enters prompt and configures settings
    ↓
AIGenerationWorker starts (background thread)
    ↓
Try Cloudie CLI first
    ↓
[If CLI available]
    CloudieCLIInterface.generate_pattern()
    ↓
    Convert output to Pattern object
    ↓
[If CLI not available]
    FallbackAIGenerator.generate_from_prompt()
    ↓
Pattern generated
    ↓
Load into Design Tools editor
```

## Configuration

### Cloudie CLI Path

The system auto-detects Cloudie CLI in:
- System PATH (`cloudie` or `cloudie-cli`)
- `~/.local/bin/cloudie`
- `~/bin/cloudie`

To specify a custom path, modify `CloudieCLIInterface.__init__()`:

```python
cli = CloudieCLIInterface(cli_path="/path/to/cloudie")
```

### API Key

If Cloudie CLI requires an API key:

```python
cli = CloudieCLIInterface(api_key="your-api-key")
```

Or set environment variable:
```bash
export CLOUDIE_API_KEY=your-api-key
```

## CLI Command Format

The integration expects Cloudie CLI to support:

```bash
cloudie generate pattern \
  --prompt "scrolling text: Hello" \
  --width 16 \
  --height 16 \
  --frames 10 \
  --style animated \
  --format json \
  --duration 100
```

### Expected Output Format (JSON)

```json
{
  "name": "AI Generated Pattern",
  "description": "Generated from prompt: scrolling text: Hello",
  "metadata": {
    "width": 16,
    "height": 16,
    "frames": 10
  },
  "frames": [
    {
      "pixels": [[255, 255, 255], [0, 0, 0], ...],
      "duration_ms": 100
    },
    ...
  ]
}
```

## Fallback Generator

When Cloudie CLI is not available, the `FallbackAIGenerator` creates patterns using rule-based logic:

- **Keyword matching**: Detects keywords in prompt (e.g., "scrolling", "bounce", "rain")
- **Simple algorithms**: Implements basic animations for common patterns
- **Deterministic**: Same prompt always generates the same pattern

### Supported Patterns

1. **Scrolling Text**: Detects "scrolling" or "text" keywords
2. **Bouncing Ball**: Detects "bounce" or "ball" keywords
3. **Rain Effect**: Detects "rain" keyword
4. **Fire Effect**: Detects "fire" or "flame" keywords
5. **Gradient**: Default fallback for other prompts

## Error Handling

- **CLI not found**: Automatically falls back to rule-based generator
- **CLI execution fails**: Shows error message, falls back to rule-based generator
- **Invalid output**: Shows error message, generation fails
- **Timeout**: 2-minute timeout for CLI execution

## Future Enhancements

1. **Multiple AI providers**: Support for other AI CLI tools (OpenAI CLI, etc.)
2. **Pattern refinement**: Iterative generation with feedback
3. **Style presets**: Pre-defined styles (retro, modern, minimalist)
4. **Batch generation**: Generate multiple variations
5. **Pattern library integration**: Save generated patterns to library
6. **Advanced prompts**: Support for complex descriptions with multiple effects

## Troubleshooting

### Cloudie CLI not detected

1. Check if CLI is installed: `cloudie --version`
2. Verify it's in PATH: `which cloudie` (Linux/Mac) or `where cloudie` (Windows)
3. Try specifying path manually in code
4. Use fallback generator (works without CLI)

### Generation fails

1. Check prompt is not empty
2. Verify matrix size is valid (1-256)
3. Check frame count is reasonable (1-1000)
4. Review error message in dialog

### Pattern looks wrong

1. Try more specific prompts
2. Adjust matrix size to match your hardware
3. Experiment with different styles
4. Use Cloudie CLI for better results (if available)

## API Reference

### `AIGenerationConfig`

```python
@dataclass
class AIGenerationConfig:
    prompt: str
    width: int = 16
    height: int = 16
    frames: int = 10
    style: str = "animated"  # "static", "animated", "scrolling", "effect"
    colors: Optional[List[Tuple[int, int, int]]] = None
    duration_ms: int = 100
    cli_path: Optional[str] = None
    api_key: Optional[str] = None
    model: str = "default"
```

### `CloudieCLIInterface`

```python
class CloudieCLIInterface:
    def __init__(self, cli_path: Optional[str] = None, api_key: Optional[str] = None)
    def generate_pattern(self, config: AIGenerationConfig, output_format: str = "json") -> Dict[str, Any]
    def convert_to_pattern(self, ai_output: Dict[str, Any]) -> Pattern
```

### `FallbackAIGenerator`

```python
class FallbackAIGenerator:
    @staticmethod
    def generate_from_prompt(config: AIGenerationConfig) -> Pattern
```

## Examples

### Basic Usage

```python
from core.ai_pattern_generator import AIGenerationConfig, CloudieCLIInterface

config = AIGenerationConfig(
    prompt="scrolling text: Hello World",
    width=16,
    height=16,
    frames=20
)

cli = CloudieCLIInterface()
ai_output = cli.generate_pattern(config)
pattern = cli.convert_to_pattern(ai_output)
```

### Using Fallback Generator

```python
from core.ai_pattern_generator import AIGenerationConfig, FallbackAIGenerator

config = AIGenerationConfig(
    prompt="bouncing ball",
    width=8,
    height=8,
    frames=30
)

pattern = FallbackAIGenerator.generate_from_prompt(config)
```

## License

This integration follows the same license as the main Upload Bridge project.

