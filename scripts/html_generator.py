"""
HTML Generator for Session Slides

Generates self-contained HTML slide decks from parsed session data.
No external dependencies - all CSS and JS embedded inline.
"""

import html
import re
from datetime import datetime
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

# Default truncation limits for long content
CODE_BLOCK_MAX_LINES = 25
CODE_BLOCK_HEAD_LINES = 8
CODE_BLOCK_TAIL_LINES = 5
PROSE_MAX_CHARS = 2000
TERMINAL_MAX_LINES = 15


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

        .code-lines {{
            color: var(--accent-light);
            font-size: 0.75rem;
            margin-left: auto;
            opacity: 0.8;
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

        /* Collapsible code blocks */
        .collapsible {{
            position: relative;
        }}

        .collapsible-toggle {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.08);
            padding: 8px 15px;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 10px;
            transition: background 0.2s ease;
        }}

        .collapsible-toggle:hover {{
            background: rgba(255, 255, 255, 0.12);
        }}

        .collapsible-toggle .toggle-label {{
            font-size: 0.85rem;
            color: var(--accent-light);
        }}

        .collapsible-toggle .toggle-icon {{
            font-size: 0.8rem;
            transition: transform 0.2s ease;
        }}

        .collapsible-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}

        .collapsible.expanded .collapsible-content {{
            max-height: 2000px;
        }}

        .collapsible.expanded .toggle-icon {{
            transform: rotate(180deg);
        }}

        /* Truncation indicator */
        .truncation-indicator {{
            background: linear-gradient(transparent, var(--code-bg));
            padding: 15px 20px 10px;
            margin-top: -10px;
            text-align: center;
            color: var(--accent-light);
            font-size: 0.85rem;
            cursor: pointer;
            border-radius: 0 0 8px 8px;
        }}

        .truncation-indicator:hover {{
            color: var(--text-light);
        }}

        /* Error highlighting in terminal output */
        .terminal-output {{
            background: #0d1117;
            border-radius: 8px;
            padding: 15px;
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 0.85rem;
            line-height: 1.5;
            overflow-x: auto;
        }}

        .terminal-line {{
            margin: 2px 0;
        }}

        .terminal-line.error {{
            color: var(--error);
            font-weight: 500;
        }}

        .terminal-line.warning {{
            color: var(--warning);
        }}

        .terminal-line.success {{
            color: var(--success);
        }}

        /* Metadata section on title slide */
        .metadata-section {{
            margin-top: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            text-align: left;
            max-width: 500px;
        }}

        .metadata-item {{
            display: flex;
            gap: 10px;
            margin: 8px 0;
            font-size: 0.9rem;
        }}

        .metadata-label {{
            color: var(--accent-light);
            min-width: 100px;
        }}

        .metadata-value {{
            color: var(--text-light);
            opacity: 0.9;
            word-break: break-all;
        }}

        /* Session Metadata Grid on Title Slide */
        .session-metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 20px;
            margin-top: 40px;
            padding: 25px 30px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-width: 700px;
        }}

        .meta-item {{
            text-align: center;
            padding: 10px;
        }}

        .meta-label {{
            display: block;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: rgba(255, 255, 255, 0.6);
            margin-bottom: 8px;
        }}

        .meta-value {{
            display: block;
            font-size: 1rem;
            font-weight: 600;
            color: var(--accent-light);
            word-break: break-word;
        }}

        .meta-value.small {{
            font-size: 0.9rem;
            font-weight: 500;
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

        // Collapsible sections
        function toggleCollapsible(element) {{
            const collapsible = element.closest('.collapsible');
            if (collapsible) {{
                collapsible.classList.toggle('expanded');
            }}
        }}

        // Initialize all collapsible toggle buttons
        document.querySelectorAll('.collapsible-toggle').forEach(toggle => {{
            toggle.addEventListener('click', function() {{
                toggleCollapsible(this);
            }});
        }});

        // Truncation indicator click to expand
        document.querySelectorAll('.truncation-indicator').forEach(indicator => {{
            indicator.addEventListener('click', function() {{
                const codeBlock = this.previousElementSibling;
                if (codeBlock && codeBlock.classList.contains('truncated-code')) {{
                    codeBlock.classList.remove('truncated-code');
                    this.style.display = 'none';
                }}
            }});
        }});

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


def format_code_block(
    code: str,
    language: str = '',
    filename: str = '',
    max_lines: int = CODE_BLOCK_MAX_LINES,
    collapsible: bool = True
) -> str:
    """
    Format a code block with syntax highlighting container.

    Handles truncation for very long code blocks with visual indicators.

    Args:
        code: The code content
        language: Programming language for the code block
        filename: Optional filename to display
        max_lines: Maximum lines before truncation (0 = no limit)
        collapsible: Whether to make long code blocks collapsible

    Returns:
        HTML string for the formatted code block
    """
    lines = code.split('\n')
    total_lines = len(lines)
    is_truncated = max_lines > 0 and total_lines > max_lines

    # Build header
    header = ''
    if language or filename or is_truncated:
        lang_html = f'<span class="code-language">{html_escape(language)}</span>' if language else ''
        file_html = f'<span class="code-filename">{html_escape(filename)}</span>' if filename else ''
        lines_info = f'<span class="code-lines">({total_lines} lines)</span>' if is_truncated else ''
        header = f'<div class="code-block-header">{lang_html}{file_html}{lines_info}</div>'

    if is_truncated and collapsible:
        # Show head + tail with truncation indicator
        head_lines = lines[:CODE_BLOCK_HEAD_LINES]
        tail_lines = lines[-CODE_BLOCK_TAIL_LINES:]
        omitted = total_lines - CODE_BLOCK_HEAD_LINES - CODE_BLOCK_TAIL_LINES

        head_code = html_escape('\n'.join(head_lines))
        tail_code = html_escape('\n'.join(tail_lines))

        truncation_msg = f'[... {omitted} more lines ...]'

        return f'''<div class="code-block collapsible">
            {header}
            <pre><code>{head_code}</code></pre>
            <div class="collapsible-toggle" onclick="toggleCollapsible(this)">
                <span class="toggle-label">{truncation_msg}</span>
                <span class="toggle-icon">&#9660;</span>
            </div>
            <div class="collapsible-content">
                <pre><code>{html_escape(chr(10).join(lines[CODE_BLOCK_HEAD_LINES:-CODE_BLOCK_TAIL_LINES]))}</code></pre>
            </div>
            <pre><code>{tail_code}</code></pre>
        </div>'''

    escaped_code = html_escape(code)
    return f'<div class="code-block">{header}<pre><code>{escaped_code}</code></pre></div>'


def is_error_line(line: str) -> bool:
    """Check if a line appears to be an error message."""
    error_indicators = [
        'error', 'Error', 'ERROR',
        'exception', 'Exception', 'EXCEPTION',
        'failed', 'Failed', 'FAILED',
        'fatal', 'Fatal', 'FATAL',
        'traceback', 'Traceback',
        'denied', 'Denied', 'DENIED',
    ]
    return any(indicator in line for indicator in error_indicators)


def is_warning_line(line: str) -> bool:
    """Check if a line appears to be a warning message."""
    warning_indicators = ['warning', 'Warning', 'WARNING', 'WARN', 'warn']
    return any(indicator in line for indicator in warning_indicators)


def is_success_line(line: str) -> bool:
    """Check if a line appears to be a success message."""
    success_indicators = ['success', 'Success', 'SUCCESS', 'passed', 'Passed', 'PASSED', 'ok', 'OK', 'done', 'Done', 'DONE']
    return any(indicator in line for indicator in success_indicators)


def format_terminal_output(output: str, max_lines: int = TERMINAL_MAX_LINES) -> str:
    """
    Format terminal output with error highlighting.

    Args:
        output: Raw terminal output
        max_lines: Maximum lines to show before truncation

    Returns:
        HTML-formatted terminal output with line classifications
    """
    if not output:
        return ''

    lines = output.strip().split('\n')
    total_lines = len(lines)
    is_truncated = max_lines > 0 and total_lines > max_lines

    # Find error lines (always show these)
    error_indices = [i for i, line in enumerate(lines) if is_error_line(line)]

    formatted_lines = []

    if is_truncated:
        # Show first few lines
        for i, line in enumerate(lines[:max_lines]):
            css_class = 'terminal-line'
            if is_error_line(line):
                css_class += ' error'
            elif is_warning_line(line):
                css_class += ' warning'
            elif is_success_line(line):
                css_class += ' success'
            formatted_lines.append(f'<div class="{css_class}">{html_escape(line)}</div>')

        # Add truncation indicator
        omitted = total_lines - max_lines
        formatted_lines.append(f'<div class="terminal-line" style="color: #888;">... ({omitted} more lines)</div>')

        # Always include error lines from the truncated portion
        for i in error_indices:
            if i >= max_lines:
                line = lines[i]
                formatted_lines.append(f'<div class="terminal-line error">{html_escape(line)}</div>')
    else:
        for line in lines:
            css_class = 'terminal-line'
            if is_error_line(line):
                css_class += ' error'
            elif is_warning_line(line):
                css_class += ' warning'
            elif is_success_line(line):
                css_class += ' success'
            formatted_lines.append(f'<div class="{css_class}">{html_escape(line)}</div>')

    return f'<div class="terminal-output">{chr(10).join(formatted_lines)}</div>'


def format_response_content(content: str, truncate_prose: bool = True) -> str:
    """
    Format response content, handling code blocks and inline formatting.

    Processes markdown-style code blocks (```language ... ```) and
    inline code (`code`), converting them to HTML.

    SECURITY: All non-code content is HTML-escaped to prevent XSS attacks.
    Code blocks and inline code are escaped within their respective handlers.

    Args:
        content: Raw response content with potential markdown formatting
        truncate_prose: Whether to truncate long prose sections

    Returns:
        HTML-formatted content string safe for embedding in HTML
    """
    if not content:
        return ''

    # Truncate very long content
    if truncate_prose and len(content) > PROSE_MAX_CHARS:
        # Find a good break point
        break_point = content.rfind('\n\n', 0, PROSE_MAX_CHARS)
        if break_point == -1:
            break_point = content.rfind('. ', 0, PROSE_MAX_CHARS)
        if break_point == -1:
            break_point = PROSE_MAX_CHARS

        truncated_content = content[:break_point]
        remaining_chars = len(content) - break_point
        content = truncated_content + f'\n\n[... {remaining_chars} more characters truncated ...]'

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


def _format_datetime(dt_string: str) -> tuple:
    """
    Parse and format a datetime string into readable date and time components.

    Converts UTC timestamps to the local timezone before formatting.

    Args:
        dt_string: ISO format datetime string or similar

    Returns:
        Tuple of (formatted_date, formatted_time) or (None, None) if parsing fails
    """
    if not dt_string:
        return None, None

    # Try Python's fromisoformat first (handles +00:00, Z, microseconds)
    dt = None
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        # Fall back to manual parsing for non-standard formats
        clean_dt = re.sub(r'[+-]\d{2}:\d{2}$', '', dt_string)
        for fmt in [
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]:
            try:
                dt = datetime.strptime(clean_dt, fmt)
                break
            except ValueError:
                continue

    if dt is None:
        return dt_string, None

    # Convert to local timezone if the datetime is timezone-aware
    if dt.tzinfo is not None:
        dt = dt.astimezone()

    # Format nicely: "February 4, 2026" and "2:30 PM"
    date_str = dt.strftime('%B %d, %Y').replace(' 0', ' ')  # Remove leading zero from day
    time_str = dt.strftime('%I:%M %p').lstrip('0')  # Remove leading zero from hour

    return date_str, time_str


def _calculate_duration(turns: list) -> str:
    """
    Calculate session duration from turn timestamps.

    Args:
        turns: List of turn dictionaries with timestamp fields

    Returns:
        Formatted duration string or None if cannot calculate
    """
    if not turns or len(turns) < 2:
        return None

    timestamps = []
    for turn in turns:
        ts = turn.get('timestamp')
        if ts:
            timestamps.append(ts)

    if len(timestamps) < 2:
        return None

    # Parse first and last timestamps
    first_dt = None
    last_dt = None
    for ts_str, target in [(timestamps[0], 'first'), (timestamps[-1], 'last')]:
        try:
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            dt = None
        if target == 'first':
            first_dt = dt
        else:
            last_dt = dt

    if first_dt is None or last_dt is None:
        return None

    # Calculate duration
    delta = last_dt - first_dt
    total_seconds = int(delta.total_seconds())

    if total_seconds < 0:
        return None

    if total_seconds < 60:
        return f'{total_seconds}s'
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        if seconds:
            return f'{minutes}m {seconds}s'
        return f'{minutes}m'
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if minutes:
            return f'{hours}h {minutes}m'
        return f'{hours}h'


def generate_title_slide(session: Dict[str, Any], title: str) -> str:
    """
    Generate the title slide HTML with elegant session metadata.

    Supports both new format (session_id, project_path, created_at at root)
    and old format (metadata dict with timestamp).

    Args:
        session: Parsed session data containing metadata and turns
        title: Title for the slide deck

    Returns:
        HTML string for the title slide
    """
    turns = session.get('turns', [])

    # Handle both new and old data formats for metadata
    # New format: session_id, project_path, created_at at root level
    # Old format: metadata dict with timestamp
    session_id = session.get('session_id', '')
    project_path = session.get('project_path', '')
    created_at = session.get('created_at', '')

    # Fall back to old format if new fields are empty
    metadata = session.get('metadata', {})
    if not created_at:
        created_at = metadata.get('timestamp', '')

    # Calculate statistics - count user turns only (turns with role='user' or has prompt)
    user_turn_count = 0
    tool_set = set()

    for turn in turns:
        # New format uses 'role' field
        role = turn.get('role', '')
        if role == 'user' or (not role and turn.get('prompt')):
            user_turn_count += 1

        # Collect tools - handle both formats
        # Old format: tools_used list of strings
        # New format: tools list of dicts with 'name' key
        tools_used = turn.get('tools_used', [])
        tools_list = turn.get('tools', [])

        for tool in tools_used:
            if isinstance(tool, str):
                tool_set.add(tool)
            elif isinstance(tool, dict):
                tool_set.add(tool.get('name', ''))

        for tool in tools_list:
            if isinstance(tool, str):
                tool_set.add(tool)
            elif isinstance(tool, dict):
                tool_set.add(tool.get('name', ''))

    tool_count = len(tool_set)

    # Use total_turns if provided (new format), otherwise count
    total_turns = session.get('total_turns', user_turn_count)

    # Parse datetime for display
    formatted_date, formatted_time = _format_datetime(created_at)

    # Get project name from path
    project_name = ''
    if project_path:
        path_parts = project_path.replace('\\', '/').rstrip('/').split('/')
        project_name = path_parts[-1] if path_parts else ''

    # Calculate duration from timestamps
    duration = _calculate_duration(turns)

    # Build subtitle with formatted date
    if formatted_date and formatted_time:
        subtitle = f'{formatted_date} at {formatted_time}'
    elif formatted_date:
        subtitle = formatted_date
    else:
        subtitle = 'Claude Code Session'

    # Build the session metadata grid
    meta_items = []

    # Session ID (abbreviated to 8 chars)
    if session_id:
        display_id = session_id[:8]
        meta_items.append(f'''
            <div class="meta-item">
                <span class="meta-label">Session</span>
                <span class="meta-value">{html_escape(display_id)}</span>
            </div>
        ''')

    # Date
    if formatted_date:
        # Shorten the date for the grid (e.g., "Feb 4, 2026")
        short_date = formatted_date
        try:
            # Try to parse and re-format to shorter version
            for fmt in ['%B %d, %Y', '%B %d %Y']:
                try:
                    dt = datetime.strptime(formatted_date.replace('  ', ' '), fmt)
                    # Use %-d on Linux/Mac, %#d on Windows to avoid leading zeros
                    try:
                        short_date = dt.strftime('%b %-d, %Y')
                    except ValueError:
                        # Fallback for Windows
                        short_date = dt.strftime('%b %d, %Y').replace(' 0', ' ')
                    break
                except ValueError:
                    continue
        except Exception:
            pass

        meta_items.append(f'''
            <div class="meta-item">
                <span class="meta-label">Date</span>
                <span class="meta-value">{html_escape(short_date)}</span>
            </div>
        ''')

    # Project name
    if project_name:
        meta_items.append(f'''
            <div class="meta-item">
                <span class="meta-label">Project</span>
                <span class="meta-value small">{html_escape(project_name)}</span>
            </div>
        ''')

    # Total turns
    meta_items.append(f'''
        <div class="meta-item">
            <span class="meta-label">Turns</span>
            <span class="meta-value">{total_turns}</span>
        </div>
    ''')

    # Duration (if calculable)
    if duration:
        meta_items.append(f'''
            <div class="meta-item">
                <span class="meta-label">Duration</span>
                <span class="meta-value">{html_escape(duration)}</span>
            </div>
        ''')

    # Tools count
    if tool_count > 0:
        meta_items.append(f'''
            <div class="meta-item">
                <span class="meta-label">Tools</span>
                <span class="meta-value">{tool_count}</span>
            </div>
        ''')

    # Build metadata HTML only if we have items
    metadata_html = ''
    if meta_items:
        metadata_html = f'''
            <div class="session-metadata">
                {''.join(meta_items)}
            </div>
        '''

    return f'''
    <div class="slide slide-title active">
        <h1>{html_escape(title)}</h1>
        <p class="subtitle">{html_escape(subtitle)}</p>
        {metadata_html}
    </div>
    '''


def generate_turn_slide(turn: Dict[str, Any], turn_index: int, total_turns: int) -> str:
    """
    Generate a content slide for a single turn.

    Supports both data formats:
    - Old format: prompt, response, tools_used (list of strings), files_modified
    - New format: content (for both user/assistant), tools (list of dicts with 'name'), role

    Args:
        turn: Turn data containing prompt/content, response, tools_used/tools, etc.
        turn_index: 1-based index of this turn
        total_turns: Total number of turns in the session

    Returns:
        HTML string for the turn slide
    """
    # Handle both data formats for prompt/content
    # Old format: 'prompt' and 'response' fields
    # New format: 'content' field with 'role' indicating user/assistant
    prompt = turn.get('prompt', '')
    response = turn.get('response', '')

    # New format uses 'content' field
    role = turn.get('role', '')
    content = turn.get('content', '')

    # If using new format, map content to prompt/response based on role
    if role == 'user' and content and not prompt:
        prompt = content
    elif role == 'assistant' and content and not response:
        response = content

    # Get title if provided (new format)
    slide_title = turn.get('title', '')

    # Handle both tool formats
    # Old format: tools_used - list of strings
    # New format: tools - list of dicts with 'name' and optionally 'description'
    tools_used = turn.get('tools_used', [])
    tools_list = turn.get('tools', [])

    # Normalize tools to list of names
    tool_names = []
    tool_descriptions = {}

    for tool in tools_used:
        if isinstance(tool, str):
            tool_names.append(tool)
        elif isinstance(tool, dict):
            name = tool.get('name', '')
            if name:
                tool_names.append(name)
                if tool.get('description'):
                    tool_descriptions[name] = tool.get('description')

    for tool in tools_list:
        if isinstance(tool, str):
            if tool not in tool_names:
                tool_names.append(tool)
        elif isinstance(tool, dict):
            name = tool.get('name', '')
            if name and name not in tool_names:
                tool_names.append(name)
                if tool.get('description'):
                    tool_descriptions[name] = tool.get('description')

    files_modified = turn.get('files_modified', [])

    # Build tools section
    tools_html = ''
    if tool_names:
        badges = []
        for tool in tool_names:
            desc = tool_descriptions.get(tool, '')
            if desc:
                badges.append(f'<span class="tool-badge" title="{html_escape(desc)}">{html_escape(tool)}</span>')
            else:
                badges.append(f'<span class="tool-badge">{html_escape(tool)}</span>')

        tools_html = f'''
        <div class="tools-section">
            <div class="tools-label">Tools Used</div>
            <div class="tool-badges">{''.join(badges)}</div>
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
    formatted_response = format_response_content(response) if response else ''

    # Build header - use title if provided, otherwise just turn number
    if slide_title:
        header_label = f'Turn {turn_index}: {html_escape(slide_title)}'
    else:
        header_label = f'Turn {turn_index}'

    # Build prompt section (only if we have a prompt)
    prompt_html = ''
    if prompt:
        prompt_html = f'''
            <div class="user-prompt">
                <div class="user-prompt-label">User Prompt</div>
                <div class="user-prompt-text">{html_escape(prompt)}</div>
            </div>
        '''

    # Build response section (only if we have a response)
    response_html = ''
    if formatted_response:
        response_html = f'''
            <div class="response-section">
                <div class="response-label">Response</div>
                <div class="response-content">
                    {formatted_response}
                </div>
            </div>
        '''

    return f'''
    <div class="slide">
        <div class="slide-content">
            <div class="slide-header">
                <span class="turn-label">{header_label}</span>
                <span class="slide-number">{turn_index} of {total_turns}</span>
            </div>

            {prompt_html}

            {tools_html}

            {response_html}

            {files_html}
        </div>
    </div>
    '''


def generate_summary_slide(session: Dict[str, Any]) -> str:
    """
    Generate the summary slide with session overview.

    Handles both data formats for tools:
    - Old format: tools_used - list of strings
    - New format: tools - list of dicts with 'name' key

    Args:
        session: Parsed session data

    Returns:
        HTML string for the summary slide
    """
    turns = session.get('turns', [])

    # Collect all tools used - handle both formats
    tool_counts: Dict[str, int] = {}
    for turn in turns:
        # Old format: tools_used list
        for tool in turn.get('tools_used', []):
            if isinstance(tool, str):
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            elif isinstance(tool, dict):
                name = tool.get('name', '')
                if name:
                    tool_counts[name] = tool_counts.get(name, 0) + 1

        # New format: tools list
        for tool in turn.get('tools', []):
            if isinstance(tool, str):
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            elif isinstance(tool, dict):
                name = tool.get('name', '')
                if name:
                    tool_counts[name] = tool_counts.get(name, 0) + 1

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


def _group_conversation_turns(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group user/assistant turns into conversation pairs.

    In the new format, turns have 'role' field (user/assistant).
    This groups them so each slide shows a user prompt with its assistant response.

    In the old format, turns already have 'prompt' and 'response' together.

    Args:
        turns: List of turn dictionaries

    Returns:
        List of grouped turns suitable for slide generation
    """
    if not turns:
        return []

    # Check if we're dealing with new format (has 'role' field)
    has_roles = any(turn.get('role') for turn in turns)

    if not has_roles:
        # Old format - already paired, return as-is
        return turns

    # New format - group user turns with following assistant turns
    grouped = []
    current_group = None

    for turn in turns:
        role = turn.get('role', '')

        if role == 'user':
            # Save any previous group
            if current_group is not None:
                grouped.append(current_group)

            # Start a new group with this user turn
            current_group = {
                'prompt': turn.get('content', ''),
                'title': turn.get('title', ''),
                'response': '',
                'tools': [],
                'tools_used': [],
                'files_modified': [],
                'timestamp': turn.get('timestamp'),
            }

        elif role == 'assistant' and current_group is not None:
            # Add assistant response to current group
            current_group['response'] = turn.get('content', '')

            # Merge tools
            for tool in turn.get('tools', []):
                current_group['tools'].append(tool)
            for tool in turn.get('tools_used', []):
                current_group['tools_used'].append(tool)

            # Merge files
            for f in turn.get('files_modified', []):
                current_group['files_modified'].append(f)

    # Don't forget the last group
    if current_group is not None:
        grouped.append(current_group)

    return grouped


def generate_html(session: Dict[str, Any], title: str = 'Session Slides') -> str:
    """
    Generate a complete HTML slide deck from parsed session data.

    Supports both data formats:
    - Old format: turns have 'prompt' and 'response' together
    - New format: turns have 'role' (user/assistant) with separate 'content'

    Args:
        session: Parsed session data containing:
            - metadata: dict with session info (timestamp, etc.) OR
            - session_id, project_path, created_at at root level (new format)
            - turns: list of turn dicts with prompt/content, response, tools_used/tools, etc.
        title: Title for the slide deck

    Returns:
        Complete self-contained HTML string
    """
    turns = session.get('turns', [])

    # Group turns if needed (for new format with separate user/assistant turns)
    grouped_turns = _group_conversation_turns(turns)

    # Generate all slides
    slides = []

    # Title slide
    slides.append(generate_title_slide(session, title))

    # Turn slides - use grouped turns for slide count
    total_turns = len(grouped_turns)
    for i, turn in enumerate(grouped_turns, 1):
        slides.append(generate_turn_slide(turn, i, total_turns))

    # Summary slide
    if grouped_turns:
        # Pass the original session (which has all turns) for accurate summary
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
    # Example usage / test with old format
    sample_session_old = {
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

    # Example with new format (from session_to_dict)
    sample_session_new = {
        'session_id': 'abc123def456',
        'project_path': '/home/user/my_project',
        'created_at': '2025-02-01T14:30:00Z',
        'total_turns': 2,
        'turns': [
            {
                'number': 1,
                'role': 'user',
                'content': 'Create a simple Python function to calculate factorial',
                'title': 'Factorial Implementation',
                'timestamp': '2025-02-01T14:30:00Z',
            },
            {
                'number': 1,
                'role': 'assistant',
                'content': '''Here's a factorial function using recursion.''',
                'tools': [
                    {'name': 'Write', 'description': 'Write: math_utils.py'},
                    {'name': 'Read', 'description': 'Read: existing_code.py'},
                ],
                'timestamp': '2025-02-01T14:30:15Z',
            },
            {
                'number': 2,
                'role': 'user',
                'content': 'Add error handling',
                'title': 'Error Handling',
                'timestamp': '2025-02-01T14:31:00Z',
            },
            {
                'number': 2,
                'role': 'assistant',
                'content': 'I\'ve added validation to check for negative numbers.',
                'tools': [
                    {'name': 'Edit', 'description': 'Edit: math_utils.py'},
                ],
                'timestamp': '2025-02-01T14:31:30Z',
            }
        ]
    }

    print("Testing old format...")
    html_output_old = generate_html(sample_session_old, 'Factorial (Old Format)')
    print(f'Generated HTML with {len(html_output_old)} characters')

    print("\nTesting new format...")
    html_output_new = generate_html(sample_session_new, 'Factorial (New Format)')
    print(f'Generated HTML with {len(html_output_new)} characters')
