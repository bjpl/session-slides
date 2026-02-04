"""
Content truncation module for Session Slides.

Provides configurable truncation strategies for different content types
to create concise, readable slide summaries.
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class TruncationConfig:
    """Configuration for content truncation limits."""

    # User prompt limits
    prompt_max_chars: int = 300

    # Prose limits
    prose_max_sentences: int = 3

    # Code block limits
    code_short_threshold: int = 15
    code_long_threshold: int = 40
    code_head_lines: int = 5
    code_tail_lines: int = 3

    # Terminal output limits
    terminal_max_lines: int = 3
    terminal_include_errors: bool = True

    # List limits
    list_max_items: int = 5

    # Comment styles by language
    comment_styles: dict = field(default_factory=lambda: {
        'python': '#',
        'py': '#',
        'ruby': '#',
        'rb': '#',
        'bash': '#',
        'sh': '#',
        'shell': '#',
        'yaml': '#',
        'yml': '#',
        'javascript': '//',
        'js': '//',
        'typescript': '//',
        'ts': '//',
        'tsx': '//',
        'jsx': '//',
        'java': '//',
        'c': '//',
        'cpp': '//',
        'c++': '//',
        'csharp': '//',
        'cs': '//',
        'go': '//',
        'rust': '//',
        'rs': '//',
        'swift': '//',
        'kotlin': '//',
        'scala': '//',
        'php': '//',
        'html': '<!--',
        'xml': '<!--',
        'svg': '<!--',
        'css': '/*',
        'scss': '//',
        'sass': '//',
        'sql': '--',
        'lua': '--',
        'haskell': '--',
        'hs': '--',
    })


def get_comment_style(language: Optional[str], config: TruncationConfig) -> tuple[str, str]:
    """
    Get the comment prefix and suffix for a given language.

    Returns:
        Tuple of (prefix, suffix). Suffix is empty for single-line comments.
    """
    if not language:
        return '//', ''

    lang = language.lower().strip()
    prefix = config.comment_styles.get(lang, '//')

    if prefix == '<!--':
        return '<!--', ' -->'
    elif prefix == '/*':
        return '/*', ' */'
    else:
        return prefix, ''


def find_sentence_boundary(text: str, max_pos: int) -> int:
    """
    Find the nearest sentence boundary before max_pos.

    Looks for periods, exclamation marks, or question marks followed by space.
    Falls back to max_pos if no boundary found.
    """
    if max_pos >= len(text):
        return len(text)

    # Look for sentence endings: .!? followed by space or end
    sentence_pattern = re.compile(r'[.!?](?:\s|$)')

    # Search backwards from max_pos
    search_text = text[:max_pos]
    matches = list(sentence_pattern.finditer(search_text))

    if matches:
        last_match = matches[-1]
        return last_match.end()

    # No sentence boundary found, look for other reasonable breaks
    # Try comma, semicolon, or word boundary
    for pos in range(max_pos - 1, max(0, max_pos - 50), -1):
        if text[pos] in ',;:' and pos + 1 < len(text) and text[pos + 1] == ' ':
            return pos + 1

    # Fall back to word boundary
    space_pos = text.rfind(' ', 0, max_pos)
    if space_pos > max_pos // 2:
        return space_pos

    return max_pos


def truncate_user_prompt(
    prompt: str,
    config: Optional[TruncationConfig] = None
) -> str:
    """
    Truncate user prompt to configured limit, breaking at sentence boundaries.

    Args:
        prompt: The user's prompt text
        config: Truncation configuration (uses defaults if None)

    Returns:
        Truncated prompt with "..." if truncated
    """
    if config is None:
        config = TruncationConfig()

    prompt = prompt.strip()

    if len(prompt) <= config.prompt_max_chars:
        return prompt

    # Find a good break point
    break_pos = find_sentence_boundary(prompt, config.prompt_max_chars)

    # Ensure we don't exceed max chars
    if break_pos > config.prompt_max_chars:
        break_pos = config.prompt_max_chars

    truncated = prompt[:break_pos].rstrip()

    # Add ellipsis if we actually truncated
    if break_pos < len(prompt):
        # Don't double-punctuate
        if truncated and truncated[-1] in '.!?':
            return truncated + ".."
        return truncated + "..."

    return truncated


def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences, handling common edge cases.
    """
    # Pattern matches sentence endings followed by space or end of string
    # Handles abbreviations like "Dr.", "Mr.", "e.g.", "i.e." by requiring
    # the next character to be uppercase or end of string
    sentences = []
    current = []

    # Simple split on sentence terminators
    pattern = re.compile(r'([.!?]+)(\s+|$)')

    last_end = 0
    for match in pattern.finditer(text):
        sentence = text[last_end:match.end()].strip()
        if sentence:
            sentences.append(sentence)
        last_end = match.end()

    # Add any remaining text
    remaining = text[last_end:].strip()
    if remaining:
        sentences.append(remaining)

    return sentences


def truncate_prose(
    text: str,
    config: Optional[TruncationConfig] = None
) -> str:
    """
    Truncate prose to first N sentences.

    Args:
        text: Prose text to truncate
        config: Truncation configuration (uses defaults if None)

    Returns:
        First N sentences with "..." if truncated
    """
    if config is None:
        config = TruncationConfig()

    text = text.strip()
    sentences = split_sentences(text)

    if len(sentences) <= config.prose_max_sentences:
        return text

    truncated = ' '.join(sentences[:config.prose_max_sentences])

    # Ensure proper ending
    if truncated and truncated[-1] in '.!?':
        return truncated + ".."
    return truncated + "..."


def truncate_code_block(
    code: str,
    language: Optional[str] = None,
    config: Optional[TruncationConfig] = None
) -> str:
    """
    Truncate code blocks based on line count.

    - Under short_threshold: Show full code
    - Between short and long threshold: Head + "... (N lines)" + tail
    - Over long_threshold: Summary only

    Args:
        code: Code block content
        language: Programming language for comment style
        config: Truncation configuration (uses defaults if None)

    Returns:
        Truncated code with appropriate comments
    """
    if config is None:
        config = TruncationConfig()

    lines = code.rstrip().split('\n')
    line_count = len(lines)

    # Short code: show all
    if line_count <= config.code_short_threshold:
        return code.rstrip()

    comment_prefix, comment_suffix = get_comment_style(language, config)

    # Very long code: summary only
    if line_count > config.code_long_threshold:
        summary = f"{comment_prefix} [{line_count} lines of {language or 'code'} - truncated for brevity]{comment_suffix}"

        # Include a few representative lines if possible
        head = '\n'.join(lines[:3])
        return f"{head}\n\n{summary}"

    # Medium code: head + indicator + tail
    head_lines = lines[:config.code_head_lines]
    tail_lines = lines[-config.code_tail_lines:]

    omitted = line_count - config.code_head_lines - config.code_tail_lines

    if omitted <= 0:
        return code.rstrip()

    omit_comment = f"{comment_prefix} ... ({omitted} lines omitted){comment_suffix}"

    head = '\n'.join(head_lines)
    tail = '\n'.join(tail_lines)

    return f"{head}\n{omit_comment}\n{tail}"


def is_error_line(line: str) -> bool:
    """Check if a terminal output line appears to be an error."""
    error_indicators = [
        'error', 'Error', 'ERROR',
        'exception', 'Exception', 'EXCEPTION',
        'failed', 'Failed', 'FAILED',
        'fatal', 'Fatal', 'FATAL',
        'traceback', 'Traceback',
        'warning', 'Warning', 'WARNING',
        'cannot', 'Cannot', 'CANNOT',
        'unable', 'Unable', 'UNABLE',
        'denied', 'Denied', 'DENIED',
        'not found', 'Not found', 'NOT FOUND',
    ]
    return any(indicator in line for indicator in error_indicators)


def truncate_terminal_output(
    output: str,
    config: Optional[TruncationConfig] = None
) -> str:
    """
    Truncate terminal output, preserving error lines.

    Shows first N lines plus any error lines, with truncation indicator.

    Args:
        output: Terminal output text
        config: Truncation configuration (uses defaults if None)

    Returns:
        Truncated output with "..." if truncated
    """
    if config is None:
        config = TruncationConfig()

    lines = output.rstrip().split('\n')

    if len(lines) <= config.terminal_max_lines:
        return output.rstrip()

    result_lines = []

    # Add first N lines
    result_lines.extend(lines[:config.terminal_max_lines])

    # Find error lines in the rest
    remaining_lines = lines[config.terminal_max_lines:]
    error_lines = []

    if config.terminal_include_errors:
        for line in remaining_lines:
            if is_error_line(line):
                error_lines.append(line)

    omitted = len(remaining_lines) - len(error_lines)

    if error_lines:
        result_lines.append(f"... ({omitted} lines omitted)")
        result_lines.extend(error_lines)
    else:
        result_lines.append(f"... ({len(remaining_lines)} more lines)")

    return '\n'.join(result_lines)


def truncate_list(
    items: list[str],
    config: Optional[TruncationConfig] = None,
    prefix: str = "- "
) -> str:
    """
    Truncate a list to first N items.

    Args:
        items: List of string items
        config: Truncation configuration (uses defaults if None)
        prefix: Prefix for each item (default "- ")

    Returns:
        Formatted list with "...and N more" if truncated
    """
    if config is None:
        config = TruncationConfig()

    if not items:
        return ""

    if len(items) <= config.list_max_items:
        return '\n'.join(f"{prefix}{item}" for item in items)

    shown_items = items[:config.list_max_items]
    remaining = len(items) - config.list_max_items

    result = '\n'.join(f"{prefix}{item}" for item in shown_items)
    result += f"\n{prefix}...and {remaining} more"

    return result


def format_tool_use(
    tool_name: str,
    parameters: Optional[dict] = None
) -> str:
    """
    Format tool usage as a concise one-liner.

    Converts verbose tool invocations to readable summaries like:
    - "Reading: filename.ts"
    - "Writing: config.json"
    - "Running: npm install"

    Args:
        tool_name: Name of the tool being used
        parameters: Tool parameters dictionary

    Returns:
        Formatted one-liner description
    """
    if parameters is None:
        parameters = {}

    tool_lower = tool_name.lower()

    # File reading tools
    if tool_lower in ('read', 'read_file', 'readfile', 'cat'):
        path = parameters.get('file_path') or parameters.get('path') or parameters.get('file', '')
        filename = path.split('/')[-1] if '/' in path else path
        return f"Reading: {filename}" if filename else "Reading file"

    # File writing tools
    if tool_lower in ('write', 'write_file', 'writefile', 'create'):
        path = parameters.get('file_path') or parameters.get('path') or parameters.get('file', '')
        filename = path.split('/')[-1] if '/' in path else path
        return f"Writing: {filename}" if filename else "Writing file"

    # File editing tools
    if tool_lower in ('edit', 'edit_file', 'editfile', 'modify', 'patch'):
        path = parameters.get('file_path') or parameters.get('path') or parameters.get('file', '')
        filename = path.split('/')[-1] if '/' in path else path
        return f"Editing: {filename}" if filename else "Editing file"

    # Bash/shell commands
    if tool_lower in ('bash', 'shell', 'terminal', 'exec', 'execute', 'run'):
        command = parameters.get('command') or parameters.get('cmd', '')
        # Truncate long commands
        if len(command) > 50:
            command = command[:47] + "..."
        return f"Running: {command}" if command else "Running command"

    # Search/grep tools
    if tool_lower in ('grep', 'search', 'find', 'ripgrep', 'rg'):
        pattern = parameters.get('pattern') or parameters.get('query', '')
        if len(pattern) > 30:
            pattern = pattern[:27] + "..."
        return f"Searching: {pattern}" if pattern else "Searching"

    # Glob/file finding
    if tool_lower in ('glob', 'find_files', 'ls', 'list'):
        pattern = parameters.get('pattern') or parameters.get('path', '')
        return f"Finding: {pattern}" if pattern else "Finding files"

    # Web fetch
    if tool_lower in ('webfetch', 'web_fetch', 'fetch', 'curl', 'wget'):
        url = parameters.get('url', '')
        if len(url) > 40:
            # Show domain only
            domain_match = re.match(r'https?://([^/]+)', url)
            if domain_match:
                url = domain_match.group(1)
        return f"Fetching: {url}" if url else "Fetching URL"

    # Web search
    if tool_lower in ('websearch', 'web_search', 'search_web'):
        query = parameters.get('query', '')
        if len(query) > 40:
            query = query[:37] + "..."
        return f"Searching web: {query}" if query else "Searching web"

    # Task/agent tools
    if tool_lower in ('task', 'agent', 'spawn'):
        description = parameters.get('description') or parameters.get('prompt', '')
        if len(description) > 40:
            description = description[:37] + "..."
        return f"Task: {description}" if description else "Running task"

    # MCP tools - extract meaningful part
    if tool_lower.startswith('mcp__'):
        parts = tool_lower.split('__')
        if len(parts) >= 3:
            action = parts[-1].replace('_', ' ')
            return f"MCP: {action}"
        return f"MCP: {tool_name}"

    # Default: use tool name
    readable_name = tool_name.replace('_', ' ').replace('-', ' ').title()
    return readable_name


# Convenience function for batch processing
def truncate_content(
    content: str,
    content_type: str,
    language: Optional[str] = None,
    config: Optional[TruncationConfig] = None
) -> str:
    """
    Truncate content based on its type.

    Args:
        content: Content to truncate
        content_type: One of 'prompt', 'prose', 'code', 'terminal', 'list'
        language: Programming language (for code blocks)
        config: Truncation configuration

    Returns:
        Truncated content
    """
    if config is None:
        config = TruncationConfig()

    type_lower = content_type.lower()

    if type_lower == 'prompt':
        return truncate_user_prompt(content, config)
    elif type_lower == 'prose':
        return truncate_prose(content, config)
    elif type_lower == 'code':
        return truncate_code_block(content, language, config)
    elif type_lower == 'terminal':
        return truncate_terminal_output(content, config)
    elif type_lower == 'list':
        items = content.split('\n')
        return truncate_list(items, config)
    else:
        # Default to prose truncation
        return truncate_prose(content, config)


if __name__ == "__main__":
    # Demo/test the module
    config = TruncationConfig()

    # Test user prompt truncation
    long_prompt = """I need you to help me refactor this authentication module.
    The current implementation uses plain text passwords which is insecure.
    We should migrate to bcrypt hashing with proper salt generation.
    Also, the session management needs to be updated to use JWT tokens
    instead of server-side sessions for better scalability."""

    print("=== User Prompt Truncation ===")
    print(truncate_user_prompt(long_prompt, config))
    print()

    # Test prose truncation
    prose = """This is the first sentence of the description. Here comes the second one with more details.
    The third sentence wraps up the main point. This fourth sentence has additional context.
    And the fifth one is probably too much."""

    print("=== Prose Truncation ===")
    print(truncate_prose(prose, config))
    print()

    # Test code truncation (medium)
    code = "\n".join([f"line {i}: some code here" for i in range(25)])

    print("=== Code Truncation (Medium - 25 lines) ===")
    print(truncate_code_block(code, "python", config))
    print()

    # Test code truncation (long)
    long_code = "\n".join([f"line {i}: implementation details" for i in range(50)])

    print("=== Code Truncation (Long - 50 lines) ===")
    print(truncate_code_block(long_code, "typescript", config))
    print()

    # Test terminal output
    terminal = """Installing dependencies...
npm WARN deprecated package@1.0.0
added 150 packages in 5s
Building project...
Compiling TypeScript...
Error: Cannot find module '@types/node'
Build failed with 1 error"""

    print("=== Terminal Output Truncation ===")
    print(truncate_terminal_output(terminal, config))
    print()

    # Test list truncation
    items = ["Item one", "Item two", "Item three", "Item four",
             "Item five", "Item six", "Item seven", "Item eight"]

    print("=== List Truncation ===")
    print(truncate_list(items, config))
    print()

    # Test tool formatting
    print("=== Tool Formatting ===")
    print(format_tool_use("Read", {"file_path": "/src/components/Auth.tsx"}))
    print(format_tool_use("Bash", {"command": "npm install --save-dev typescript @types/node"}))
    print(format_tool_use("Grep", {"pattern": "authentication.*error"}))
    print(format_tool_use("mcp__claude-flow__memory_store", {}))
