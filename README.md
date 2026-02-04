# session-slides

Convert Claude Code session transcripts into navigable HTML slide presentations.

## Installation

```bash
npm install -g @bjpl/session-slides
```

Requires Python 3.8 or later.

## Usage

```bash
# Generate slides from the current project's most recent session
session-slides

# Open in browser immediately
session-slides --open

# Generate from a specific session file
session-slides --from ~/.claude/projects/.../session.jsonl

# Custom title and output path
session-slides --title "Building the Auth System" --output slides.html
```

Output defaults to `./session-slides/{timestamp}.html` in your current directory. Each run is preserved.

## Options

| Option | Description |
|--------|-------------|
| `--from PATH` | Path to session JSONL file (auto-detects if omitted) |
| `--output PATH` | Output HTML file path (default: `./session-slides/{timestamp}.html`) |
| `--title TEXT` | Custom presentation title |
| `--open` | Open in browser after generation |
| `--ai-titles` | Use Ollama for slide titles (requires local Ollama) |
| `--clean` | Remove previous timestamped output files |
| `--verbose` | Enable verbose output |

## Output

Generates a self-contained HTML file with:

- Title slide with session metadata
- One slide per conversation turn
- Intelligent titles extracted from your prompts
- Tool usage indicators (Read, Write, Bash, etc.)
- Code blocks with syntax highlighting
- Summary slide with statistics

The HTML has no external dependencies and works offline.

## How It Works

1. Parses Claude Code's JSONL session format
2. Extracts conversation turns and tool usage
3. Generates titles using pattern matching (390+ action verbs)
4. Builds a responsive HTML presentation with keyboard navigation

## Session Files

Claude Code stores sessions in `~/.claude/projects/`. Each project directory contains JSONL files with your conversation history. The tool automatically finds the most recent session for your current working directory.

## Requirements

- Node.js 14+
- Python 3.8+

## License

MIT
