"""
Session Slides Scripts Package

This package contains the core modules for parsing Claude Code sessions
and generating presentation slides.
"""

from .parser import (
    # Data classes
    ToolUse,
    ContentBlock,
    Turn,
    Session,
    # Core parsing functions
    parse_jsonl,
    extract_turns,
    load_session,
    # Session finding
    find_current_session,
    find_all_sessions,
    # Path utilities
    encode_path,
    decode_path,
    get_project_path_from_session,
    # Summary
    get_session_summary,
    # Constants
    CLAUDE_PROJECTS_DIR,
)

__all__ = [
    # Data classes
    "ToolUse",
    "ContentBlock",
    "Turn",
    "Session",
    # Core parsing functions
    "parse_jsonl",
    "extract_turns",
    "load_session",
    # Session finding
    "find_current_session",
    "find_all_sessions",
    # Path utilities
    "encode_path",
    "decode_path",
    "get_project_path_from_session",
    # Summary
    "get_session_summary",
    # Constants
    "CLAUDE_PROJECTS_DIR",
]

__version__ = "0.1.0"
