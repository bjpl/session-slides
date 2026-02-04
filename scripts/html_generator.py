"""
HTML Generator for Session Slides

Generates self-contained HTML slide decks from parsed session data.
No external dependencies - all CSS and JS embedded inline.
"""

import html
import re
from typing import Dict, List, Any, Optional


# CSS Variables
CSS_VARS = {
    'bg_dark': '#1a1a2e',
    'bg_darker': '#16213e',
    'accent': '#4a6cf7',
    'accent_light': '#6b8cff',
    'user_bg': '#e3f2fd',
    'user_border': '#2196f3',
    'code_bg': '#1e1e1e',
    'code_text': '#d4d4d4',
    'text_primary': '#333333',
    'text_secondary': '#666666',
    'text_light': '#ffffff',
    'card_bg': '#f8f9fa',
    'border_color': '#e0e0e0',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
}


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;">
    <title>{title}</title>
    <style>
        :root {{
            --bg-dark: {bg_dark};
            --bg-darker: {bg_darker};
            --accent: {accent};
            --accent-light: {accent_light};
            --user-bg: {user_bg};
            --user-border: {user_border};
            --code-bg: {code_bg};
            --code-text: {code_text};
            --text-primary: {text_primary};
            --text-secondary: {text_secondary};
            --text-light: {text_light};
            --card-bg: {card_bg};
            --border-color: {border_color};
            --success: {success};
            --warning: {warning};
            --error: {error};
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            color: var(--text-primary);
            line-height: 1.6;
        }}

        .slide-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        .slide {{
            display: none;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            min-height: 80vh;
            overflow: hidden;
        }}

        .slide.active {{
            display: block;
        }}

        /* Title Slide */
        .slide-title {{
            background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-darker) 100%);
            color: var(--text-light);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 60px 40px;
        }}

        .slide-title h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 20px;
            background: linear-gradient(135deg, var(--text-light) 0%, var(--accent-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .slide-title .subtitle {{
            font-size: 1.4rem;
            opacity: 0.9;
            margin-bottom: 40px;
        }}

        .slide-title .stats {{
            display: flex;
            gap: 40px;
            margin-top: 30px;
        }}

        .slide-title .stat {{
            text-align: center;
        }}

        .slide-title .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent-light);
        }}

        .slide-title .stat-label {{
            font-size: 0.9rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* Content Slides */
        .slide-content {{
            padding: 40px;
        }}

        .slide-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--border-color);
        }}

        .turn-label {{
            background: var(--accent);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .slide-number {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        /* User Prompt Box */
        .user-prompt {{
            background: var(--user-bg);
            border-left: 4px solid var(--user-border);
            padding: 20px 25px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 25px;
        }}

        .user-prompt-label {{
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--user-border);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .user-prompt-text {{
            font-size: 1.1rem;
            color: var(--text-primary);
        }}

        /* Tool Badges */
        .tools-section {{
            margin: 20px 0;
        }}

        .tools-label {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 10px;
        }}

        .tool-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .tool-badge {{
            background: var(--bg-dark);
            color: var(--text-light);
            padding: 6px 14px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-family: 'SF Mono', 'Consolas', monospace;
        }}

        /* Response Content */
        .response-section {{
            margin-top: 25px;
        }}

        .response-label {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 10px;
        }}

        .response-content {{
            font-size: 1rem;
            line-height: 1.8;
            color: var(--text-primary);
        }}

        .response-content p {{
            margin-bottom: 15px;
        }}

        .response-content ul, .response-content ol {{
            margin: 15px 0;
            padding-left: 25px;
        }}

        .response-content li {{
            margin-bottom: 8px;
        }}

        /* Code Blocks */
        .code-block {{
            background: var(--code-bg);
            color: var(--code-text);
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            overflow-x: auto;
            font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
        }}

        .code-block-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.05);
            margin: -20px -20px 15px -20px;
            padding: 10px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .code-language {{
            color: var(--accent-light);
            font-size: 0.8rem;
            text-transform: uppercase;
        }}

        .code-filename {{
            color: var(--text-secondary);
            font-size: 0.8rem;
        }}

        code {{
            font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
        }}

        /* Inline code */
        .inline-code {{
            background: rgba(0, 0, 0, 0.06);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9em;
        }}

        /* Summary Slide */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}

        .summary-card {{
            background: var(--card-bg);
            border-radius: 10px;
            padding: 25px;
            border: 1px solid var(--border-color);
        }}

        .summary-card h3 {{
            font-size: 1.1rem;
            margin-bottom: 15px;
            color: var(--accent);
        }}

        .summary-card ul {{
            list-style: none;
        }}

        .summary-card li {{
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.95rem;
        }}

        .summary-card li:last-child {{
            border-bottom: none;
        }}

        /* Files Section */
        .files-section {{
            margin-top: 20px;
        }}

        .file-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            background: var(--card-bg);
            border-radius: 6px;
            margin-bottom: 8px;
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 0.85rem;
        }}

        .file-icon {{
            color: var(--accent);
        }}

        .file-action {{
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 10px;
            text-transform: uppercase;
        }}

        .file-action.created {{
            background: rgba(76, 175, 80, 0.1);
            color: var(--success);
        }}

        .file-action.modified {{
            background: rgba(255, 152, 0, 0.1);
            color: var(--warning);
        }}

        .file-action.deleted {{
            background: rgba(244, 67, 54, 0.1);
            color: var(--error);
        }}

        /* Navigation */
        .navigation {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 20px;
            background: white;
            padding: 15px 30px;
            border-radius: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            z-index: 1000;
        }}

        .nav-button {{
            background: var(--bg-dark);
            color: white;
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }}

        .nav-button:hover {{
            background: var(--accent);
            transform: scale(1.1);
        }}

        .nav-button:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
            transform: none;
        }}

        .nav-counter {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            min-width: 80px;
            text-align: center;
        }}

        /* Progress Bar */
        .progress-bar {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--border-color);
            z-index: 1001;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--accent-light));
            transition: width 0.3s ease;
        }}

        /* Keyboard hints */
        .keyboard-hints {{
            position: fixed;
            bottom: 100px;
            right: 30px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            font-size: 0.8rem;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .keyboard-hints.visible {{
            opacity: 1;
        }}

        .keyboard-hints kbd {{
            background: rgba(255, 255, 255, 0.2);
            padding: 3px 8px;
            border-radius: 4px;
            margin: 0 3px;
        }}

        /* Truncated content */
        .truncated {{
            position: relative;
        }}

        .truncated::after {{
            content: '...';
            color: var(--text-secondary);
        }}

        .expand-button {{
            color: var(--accent);
            cursor: pointer;
            font-size: 0.85rem;
            margin-top: 10px;
            display: inline-block;
        }}

        .expand-button:hover {{
            text-decoration: underline;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .slide-container {{
                padding: 10px;
            }}

            .slide-content {{
                padding: 20px;
            }}

            .slide-title h1 {{
                font-size: 2rem;
            }}

            .slide-title .stats {{
                flex-direction: column;
                gap: 20px;
            }}

            .navigation {{
                padding: 10px 20px;
            }}

            .nav-button {{
                width: 40px;
                height: 40px;
            }}
        }}
    </style>
</head>
<body>
    <div class="progress-bar">
        <div class="progress-fill" id="progress"></div>
    </div>

    <div class="slide-container">
        {slides}
    </div>

    <div class="navigation">
        <button class="nav-button" id="prev-btn" onclick="prevSlide()">&#8592;</button>
        <span class="nav-counter" id="counter">1 / {total_slides}</span>
        <button class="nav-button" id="next-btn" onclick="nextSlide()">&#8594;</button>
    </div>

    <div class="keyboard-hints" id="hints">
        Use <kbd>&#8592;</kbd> <kbd>&#8594;</kbd> or <kbd>Space</kbd> to navigate
    </div>

    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        const counter = document.getElementById('counter');
        const progress = document.getElementById('progress');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const hints = document.getElementById('hints');

        function showSlide(index) {{
            if (index < 0) index = 0;
            if (index >= totalSlides) index = totalSlides - 1;

            slides.forEach((slide, i) => {{
                slide.classList.toggle('active', i === index);
            }});

            currentSlide = index;
            counter.textContent = `${{index + 1}} / ${{totalSlides}}`;
            progress.style.width = `${{((index + 1) / totalSlides) * 100}}%`;

            prevBtn.disabled = index === 0;
            nextBtn.disabled = index === totalSlides - 1;
        }}

        function nextSlide() {{
            showSlide(currentSlide + 1);
        }}

        function prevSlide() {{
            showSlide(currentSlide - 1);
        }}

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === ' ') {{
                e.preventDefault();
                nextSlide();
            }} else if (e.key === 'ArrowLeft') {{
                e.preventDefault();
                prevSlide();
            }} else if (e.key === 'Home') {{
                e.preventDefault();
                showSlide(0);
            }} else if (e.key === 'End') {{
                e.preventDefault();
                showSlide(totalSlides - 1);
            }}
        }});

        // Show keyboard hints on first load
        setTimeout(() => {{
            hints.classList.add('visible');
            setTimeout(() => {{
                hints.classList.remove('visible');
            }}, 3000);
        }}, 1000);

        // Initialize
        showSlide(0);
    </script>
</body>
</html>
'''


def html_escape(text: str) -> str:
    """
    Escape special HTML characters in text.

    Args:
        text: Raw text that may contain HTML special characters

    Returns:
        HTML-escaped text safe for embedding in HTML
    """
    if not text:
        return ''
    return html.escape(str(text))


def format_code_block(code: str, language: str = '', filename: str = '') -> str:
    """
    Format a code block with syntax highlighting container.

    Args:
        code: The code content
        language: Programming language for the code block
        filename: Optional filename to display

    Returns:
        HTML string for the formatted code block
    """
    escaped_code = html_escape(code)

    header = ''
    if language or filename:
        lang_html = f'<span class="code-language">{html_escape(language)}</span>' if language else ''
        file_html = f'<span class="code-filename">{html_escape(filename)}</span>' if filename else ''
        header = f'<div class="code-block-header">{lang_html}{file_html}</div>'

    return f'<div class="code-block">{header}<pre><code>{escaped_code}</code></pre></div>'


def format_response_content(content: str) -> str:
    """
    Format response content, handling code blocks and inline formatting.

    Processes markdown-style code blocks (```language ... ```) and
    inline code (`code`), converting them to HTML.

    SECURITY: All non-code content is HTML-escaped to prevent XSS attacks.
    Code blocks and inline code are escaped within their respective handlers.

    Args:
        content: Raw response content with potential markdown formatting

    Returns:
        HTML-formatted content string safe for embedding in HTML
    """
    if not content:
        return ''

    # Use placeholders for code blocks to protect them during escaping
    code_blocks = []
    code_block_pattern = r'```(\w*)\n?([\s\S]*?)```'

    def extract_code_block(match):
        language = match.group(1) or ''
        code = match.group(2).rstrip()
        placeholder = f'\x00CODE_BLOCK_{len(code_blocks)}\x00'
        code_blocks.append(format_code_block(code, language))
        return placeholder

    result = re.sub(code_block_pattern, extract_code_block, content)

    # Extract inline code with placeholders
    inline_codes = []
    inline_code_pattern = r'`([^`]+)`'

    def extract_inline_code(match):
        placeholder = f'\x00INLINE_CODE_{len(inline_codes)}\x00'
        inline_codes.append(f'<code class="inline-code">{html_escape(match.group(1))}</code>')
        return placeholder

    result = re.sub(inline_code_pattern, extract_inline_code, result)

    # NOW escape all remaining content (this is the critical security fix)
    result = html_escape(result)

    # Restore code blocks (they were already escaped internally)
    for i, block in enumerate(code_blocks):
        result = result.replace(f'\x00CODE_BLOCK_{i}\x00', block)

    # Restore inline codes (they were already escaped internally)
    for i, code in enumerate(inline_codes):
        result = result.replace(f'\x00INLINE_CODE_{i}\x00', code)

    # Convert newlines to paragraphs for non-code content
    # Split by code blocks to preserve their formatting
    parts = re.split(r'(<div class="code-block">[\s\S]*?</div>)', result)

    formatted_parts = []
    for part in parts:
        if part.startswith('<div class="code-block">'):
            formatted_parts.append(part)
        else:
            # Convert double newlines to paragraph breaks
            paragraphs = re.split(r'\n\n+', part.strip())
            for p in paragraphs:
                if p.strip():
                    # Convert single newlines to <br> within paragraphs
                    # Note: &lt;br&gt; would have been escaped, so use actual <br>
                    p_with_breaks = p.replace('\n', '<br>\n')
                    formatted_parts.append(f'<p>{p_with_breaks}</p>')

    return '\n'.join(formatted_parts)


def generate_title_slide(session: Dict[str, Any], title: str) -> str:
    """
    Generate the title slide HTML.

    Args:
        session: Parsed session data containing metadata and turns
        title: Title for the slide deck

    Returns:
        HTML string for the title slide
    """
    metadata = session.get('metadata', {})
    turns = session.get('turns', [])

    # Calculate statistics
    turn_count = len(turns)
    tool_set = set()
    for turn in turns:
        for tool in turn.get('tools_used', []):
            tool_set.add(tool)
    tool_count = len(tool_set)

    # Get timestamp if available
    timestamp = metadata.get('timestamp', '')
    subtitle = f'Session recorded: {timestamp}' if timestamp else 'Claude Code Session'

    return f'''
    <div class="slide slide-title active">
        <h1>{html_escape(title)}</h1>
        <p class="subtitle">{html_escape(subtitle)}</p>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{turn_count}</div>
                <div class="stat-label">Turns</div>
            </div>
            <div class="stat">
                <div class="stat-value">{tool_count}</div>
                <div class="stat-label">Tools Used</div>
            </div>
        </div>
    </div>
    '''


def generate_turn_slide(turn: Dict[str, Any], turn_index: int, total_turns: int) -> str:
    """
    Generate a content slide for a single turn.

    Args:
        turn: Turn data containing prompt, response, tools_used, etc.
        turn_index: 1-based index of this turn
        total_turns: Total number of turns in the session

    Returns:
        HTML string for the turn slide
    """
    prompt = turn.get('prompt', '')
    response = turn.get('response', '')
    tools_used = turn.get('tools_used', [])
    files_modified = turn.get('files_modified', [])

    # Build tools section
    tools_html = ''
    if tools_used:
        badges = ''.join(
            f'<span class="tool-badge">{html_escape(tool)}</span>'
            for tool in tools_used
        )
        tools_html = f'''
        <div class="tools-section">
            <div class="tools-label">Tools Used</div>
            <div class="tool-badges">{badges}</div>
        </div>
        '''

    # Build files section
    files_html = ''
    if files_modified:
        file_items = []
        for file_info in files_modified:
            if isinstance(file_info, dict):
                path = file_info.get('path', '')
                action = file_info.get('action', 'modified')
            else:
                path = str(file_info)
                action = 'modified'

            file_items.append(f'''
                <div class="file-item">
                    <span class="file-icon">&#128196;</span>
                    <span>{html_escape(path)}</span>
                    <span class="file-action {action}">{action}</span>
                </div>
            ''')

        files_html = f'''
        <div class="files-section">
            <div class="tools-label">Files Modified</div>
            {''.join(file_items)}
        </div>
        '''

    # Format response content
    formatted_response = format_response_content(response)

    return f'''
    <div class="slide">
        <div class="slide-content">
            <div class="slide-header">
                <span class="turn-label">Turn {turn_index}</span>
                <span class="slide-number">{turn_index} of {total_turns}</span>
            </div>

            <div class="user-prompt">
                <div class="user-prompt-label">User Prompt</div>
                <div class="user-prompt-text">{html_escape(prompt)}</div>
            </div>

            {tools_html}

            <div class="response-section">
                <div class="response-label">Response</div>
                <div class="response-content">
                    {formatted_response}
                </div>
            </div>

            {files_html}
        </div>
    </div>
    '''


def generate_summary_slide(session: Dict[str, Any]) -> str:
    """
    Generate the summary slide with session overview.

    Args:
        session: Parsed session data

    Returns:
        HTML string for the summary slide
    """
    turns = session.get('turns', [])

    # Collect all tools used
    all_tools = []
    for turn in turns:
        all_tools.extend(turn.get('tools_used', []))
    tool_counts = {}
    for tool in all_tools:
        tool_counts[tool] = tool_counts.get(tool, 0) + 1

    # Sort by count
    sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)

    # Collect all files modified
    all_files = []
    for turn in turns:
        for file_info in turn.get('files_modified', []):
            if isinstance(file_info, dict):
                path = file_info.get('path', '')
            else:
                path = str(file_info)
            if path and path not in all_files:
                all_files.append(path)

    # Build tools summary
    tools_items = ''.join(
        f'<li>{html_escape(tool)} ({count}x)</li>'
        for tool, count in sorted_tools[:10]
    )

    # Build files summary
    files_items = ''.join(
        f'<li>{html_escape(path)}</li>'
        for path in all_files[:10]
    )

    more_files = ''
    if len(all_files) > 10:
        more_files = f'<li>... and {len(all_files) - 10} more</li>'

    return f'''
    <div class="slide">
        <div class="slide-content">
            <div class="slide-header">
                <span class="turn-label">Summary</span>
                <span class="slide-number">Session Overview</span>
            </div>

            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Tools Used ({len(sorted_tools)} unique)</h3>
                    <ul>
                        {tools_items}
                    </ul>
                </div>

                <div class="summary-card">
                    <h3>Files Modified ({len(all_files)} total)</h3>
                    <ul>
                        {files_items}
                        {more_files}
                    </ul>
                </div>
            </div>
        </div>
    </div>
    '''


def generate_html(session: Dict[str, Any], title: str = 'Session Slides') -> str:
    """
    Generate a complete HTML slide deck from parsed session data.

    Args:
        session: Parsed session data containing:
            - metadata: dict with session info (timestamp, etc.)
            - turns: list of turn dicts with prompt, response, tools_used, files_modified
        title: Title for the slide deck

    Returns:
        Complete self-contained HTML string
    """
    turns = session.get('turns', [])

    # Generate all slides
    slides = []

    # Title slide
    slides.append(generate_title_slide(session, title))

    # Turn slides
    for i, turn in enumerate(turns, 1):
        slides.append(generate_turn_slide(turn, i, len(turns)))

    # Summary slide
    if turns:
        slides.append(generate_summary_slide(session))

    # Combine all slides
    slides_html = '\n'.join(slides)
    total_slides = len(slides)

    # Fill in the template
    return HTML_TEMPLATE.format(
        title=html_escape(title),
        slides=slides_html,
        total_slides=total_slides,
        **CSS_VARS
    )


if __name__ == '__main__':
    # Example usage / test
    sample_session = {
        'metadata': {
            'timestamp': '2025-01-31T10:30:00Z'
        },
        'turns': [
            {
                'prompt': 'Create a simple Python function to calculate factorial',
                'response': '''Here's a factorial function:

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

This uses recursion to calculate the factorial.''',
                'tools_used': ['Write', 'Read'],
                'files_modified': [{'path': 'math_utils.py', 'action': 'created'}]
            },
            {
                'prompt': 'Add error handling',
                'response': 'I\'ve added validation to check for negative numbers and non-integers.',
                'tools_used': ['Edit'],
                'files_modified': [{'path': 'math_utils.py', 'action': 'modified'}]
            }
        ]
    }

    html_output = generate_html(sample_session, 'Factorial Function Development')
    print(f'Generated HTML with {len(html_output)} characters')
