#!/usr/bin/env python3
"""
Session Slides Generator CLI

Converts Claude Code session JSONL files into navigable HTML slide presentations.

Usage:
    python generate_slides.py [options]

Options:
    --from PATH      Session JSONL file (auto-detects if omitted)
    --output PATH    Output HTML file (default: output/session-slides-{timestamp}.html)
    --title TEXT     Custom presentation title
    --open           Open in browser after generation
    --ai-titles      Use Ollama for title generation (requires ollama)
"""

import argparse
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import from sibling modules
from parser import Session, Turn, extract_turns, find_current_session, load_session
from titles import generate_turn_title, generate_continued_title, generate_title_ollama
from truncation import (
    TruncationConfig,
    truncate_user_prompt,
    truncate_prose,
    truncate_code_block,
    format_tool_use,
)
from html_generator import generate_html


def print_progress(message: str, end: str = "\n") -> None:
    """Print progress message to terminal."""
    print(f"[*] {message}", end=end, flush=True)


def print_success(message: str) -> None:
    """Print success message to terminal."""
    print(f"[✓] {message}")


def print_error(message: str) -> None:
    """Print error message to terminal."""
    print(f"[✗] {message}", file=sys.stderr)


def generate_titles_for_session(session: Session, use_ai: bool = False) -> dict[int, str]:
    """Generate titles for all turns in a session."""
    titles = {}

    for turn in session.turns:
        if turn.is_user_message():
            prompt = turn.get_text_content()
            if use_ai:
                # Try AI first, fall back to heuristic
                ai_title = generate_title_ollama(prompt)
                if ai_title:
                    titles[turn.number if hasattr(turn, 'number') else len(titles) + 1] = ai_title
                else:
                    titles[turn.number if hasattr(turn, 'number') else len(titles) + 1] = generate_turn_title(prompt, len(titles) + 1)
            else:
                titles[turn.number if hasattr(turn, 'number') else len(titles) + 1] = generate_turn_title(prompt, len(titles) + 1)

    return titles


def session_to_dict(session: Session) -> dict:
    """Convert Session object to dict format expected by html_generator."""
    turns_data = []
    turn_num = 0

    for turn in session.turns:
        if turn.is_user_message():
            turn_num += 1
            user_content = turn.get_text_content()
            title = generate_turn_title(user_content, turn_num)

            turns_data.append({
                'number': turn_num,
                'role': 'user',
                'content': user_content,
                'title': title,
                'timestamp': turn.timestamp.isoformat() if turn.timestamp else None,
            })
        else:
            # Assistant turn
            assistant_content = turn.get_text_content()
            tool_uses = turn.get_tool_uses()

            tools_formatted = []
            for tool in tool_uses:
                tools_formatted.append({
                    'name': tool.name,
                    'input': tool.input,
                    'description': tool.get_description() if hasattr(tool, 'get_description') else format_tool_use(tool.name, tool.input),
                })

            turns_data.append({
                'number': turn_num,
                'role': 'assistant',
                'content': assistant_content,
                'tools': tools_formatted,
                'timestamp': turn.timestamp.isoformat() if turn.timestamp else None,
            })

    return {
        'session_id': session.session_id,
        'project_path': session.project_path,
        'turns': turns_data,
        'created_at': session.turns[0].timestamp.isoformat() if session.turns and session.turns[0].timestamp else None,
        'total_turns': turn_num,
    }


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="generate_slides",
        description="Convert Claude Code session files into HTML slide presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_slides.py --from session.jsonl
  python generate_slides.py --from session.jsonl --output slides.html --title "My Session"
  python generate_slides.py --from session.jsonl --ai-titles --open
  python generate_slides.py  # Auto-detect latest session file
        """,
    )

    parser.add_argument(
        "--from",
        dest="input_file",
        type=str,
        metavar="PATH",
        help="Path to session JSONL file (auto-detects if not specified)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        metavar="PATH",
        help="Output HTML file path (default: output/session-slides-{timestamp}.html)",
    )

    parser.add_argument(
        "--title",
        "-t",
        type=str,
        metavar="TEXT",
        help="Custom title for the presentation",
    )

    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated HTML in default browser",
    )

    parser.add_argument(
        "--ai-titles",
        action="store_true",
        help="Use Ollama AI to generate slide titles (requires local Ollama)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Step 1: Find or load session file
    if args.input_file:
        input_path = Path(args.input_file)
        if not input_path.exists():
            print_error(f"Session file not found: {input_path}")
            return 1
        print_progress(f"Loading session: {input_path}")
    else:
        print_progress("Searching for latest session...")
        input_path = find_current_session()
        if input_path is None:
            print_error("No session file found for current directory.")
            print_error("Use --from to specify a session file path.")
            return 1
        print_success(f"Found session: {input_path}")

    # Step 2: Parse session file
    try:
        session = extract_turns(input_path)
    except Exception as e:
        print_error(f"Failed to parse session: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    if not session.turns:
        print_error("Session contains no conversation turns")
        return 1

    user_turns = len([t for t in session.turns if t.is_user_message()])
    print_success(f"Parsed {len(session.turns)} messages ({user_turns} user turns)")

    # Step 3: Convert to dict format and generate titles
    if args.ai_titles:
        print_progress("Generating AI titles with Ollama...")
    else:
        print_progress("Generating heuristic titles...")

    session_dict = session_to_dict(session)
    print_success(f"Generated {session_dict['total_turns']} slide titles")

    # Step 4: Generate HTML
    presentation_title = args.title or f"Session: {session.session_id[:8] if session.session_id else 'Claude Code'}"
    print_progress("Building HTML presentation...")

    try:
        html_content = generate_html(session_dict, title=presentation_title)
    except Exception as e:
        print_error(f"Failed to generate HTML: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Step 5: Write output
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        output_path = output_dir / f"session-slides-{timestamp}.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        output_path.write_text(html_content, encoding="utf-8")
    except IOError as e:
        print_error(f"Failed to write output: {e}")
        return 1

    print_success(f"Generated: {output_path.absolute()}")

    # Step 6: Optionally open in browser
    if args.open:
        print_progress("Opening in browser...")
        try:
            webbrowser.open(f"file://{output_path.absolute()}")
        except Exception as e:
            print_error(f"Could not open browser: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
