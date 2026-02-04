"""
Session Slides JSONL Parser Module

Parses Claude Code session JSONL files into structured data for slide generation.
Handles all message types: user, assistant, tool_use, tool_result, system, progress.

Path Encoding Notes:
    Claude Code encodes project paths by replacing both / and _ with - in directory names.
    Example: /mnt/c/Users/brand/Project_Workspace -> -mnt-c-Users-brand-Project-Workspace

    This makes decoding ambiguous (can't distinguish / from _), so:
    - For path matching: we encode the input path and compare encoded forms
    - For display: we use the cwd field from the session JSON which has the original path
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional


# Claude projects directory location
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


@dataclass
class ToolUse:
    """Represents a tool use action in a Claude Code session."""

    id: str
    name: str
    input: dict[str, Any]
    result: Optional[str] = None
    is_error: bool = False

    @classmethod
    def from_content_block(cls, block: dict[str, Any]) -> ToolUse:
        """Create ToolUse from an assistant message content block."""
        return cls(
            id=block.get("id", ""),
            name=block.get("name", ""),
            input=block.get("input", {}),
        )

    def get_description(self) -> str:
        """Get a human-readable description of the tool use."""
        desc = self.input.get("description", "")
        if desc:
            return desc

        # Generate description based on tool type
        if self.name == "Bash":
            cmd = self.input.get("command", "")
            return f"Run: {cmd[:80]}{'...' if len(cmd) > 80 else ''}"
        elif self.name == "Read":
            return f"Read: {self.input.get('file_path', 'file')}"
        elif self.name == "Write":
            return f"Write: {self.input.get('file_path', 'file')}"
        elif self.name == "Edit":
            return f"Edit: {self.input.get('file_path', 'file')}"
        elif self.name == "Glob":
            return f"Search: {self.input.get('pattern', 'files')}"
        elif self.name == "Grep":
            return f"Search for: {self.input.get('pattern', 'pattern')}"
        elif self.name == "WebFetch":
            return f"Fetch: {self.input.get('url', 'url')}"
        elif self.name == "WebSearch":
            return f"Search: {self.input.get('query', 'query')}"
        else:
            return f"{self.name}"


@dataclass
class ContentBlock:
    """Represents a content block in an assistant message."""

    type: str  # text, tool_use, thinking
    text: Optional[str] = None
    tool_use: Optional[ToolUse] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContentBlock:
        """Create ContentBlock from a dictionary."""
        block_type = data.get("type", "")

        if block_type == "text":
            return cls(type="text", text=data.get("text", ""), raw=data)
        elif block_type == "tool_use":
            return cls(
                type="tool_use",
                tool_use=ToolUse.from_content_block(data),
                raw=data,
            )
        elif block_type == "thinking":
            return cls(type="thinking", text=data.get("thinking", ""), raw=data)
        elif block_type == "tool_result":
            return cls(type="tool_result", text=data.get("content", ""), raw=data)
        else:
            return cls(type=block_type, raw=data)


@dataclass
class Turn:
    """Represents a single turn in the conversation (user or assistant)."""

    role: str  # user, assistant, system
    uuid: str
    timestamp: datetime
    session_id: str
    parent_uuid: Optional[str] = None

    # Content can be string (user text) or list of ContentBlocks (assistant)
    content: str | list[ContentBlock] = ""

    # Metadata
    model: Optional[str] = None
    cwd: Optional[str] = None
    git_branch: Optional[str] = None

    # For system messages
    subtype: Optional[str] = None

    # For tracking tool results
    tool_results: dict[str, str] = field(default_factory=dict)

    # Raw data for debugging
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_jsonl_entry(cls, entry: dict[str, Any]) -> Optional[Turn]:
        """Create Turn from a JSONL entry. Returns None for non-turn entries."""
        entry_type = entry.get("type", "")

        # Skip non-turn entries
        if entry_type in ("file-history-snapshot", "progress"):
            return None

        # Get common fields
        uuid = entry.get("uuid", "")
        parent_uuid = entry.get("parentUuid")
        session_id = entry.get("sessionId", "")
        cwd = entry.get("cwd")
        git_branch = entry.get("gitBranch")

        # Parse timestamp
        ts_str = entry.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.now()

        # Handle different entry types
        if entry_type == "user":
            message = entry.get("message", {})
            content = message.get("content", "")

            # Content can be string or list (for tool results)
            if isinstance(content, list):
                # Parse tool results
                blocks = [ContentBlock.from_dict(b) for b in content]
                return cls(
                    role="user",
                    uuid=uuid,
                    timestamp=timestamp,
                    session_id=session_id,
                    parent_uuid=parent_uuid,
                    content=blocks,
                    cwd=cwd,
                    git_branch=git_branch,
                    raw=entry,
                )
            else:
                return cls(
                    role="user",
                    uuid=uuid,
                    timestamp=timestamp,
                    session_id=session_id,
                    parent_uuid=parent_uuid,
                    content=str(content),
                    cwd=cwd,
                    git_branch=git_branch,
                    raw=entry,
                )

        elif entry_type == "assistant":
            message = entry.get("message", {})
            content = message.get("content", [])
            model = message.get("model")

            # Parse content blocks
            if isinstance(content, list):
                blocks = [ContentBlock.from_dict(b) for b in content]
            else:
                blocks = [ContentBlock(type="text", text=str(content))]

            return cls(
                role="assistant",
                uuid=uuid,
                timestamp=timestamp,
                session_id=session_id,
                parent_uuid=parent_uuid,
                content=blocks,
                model=model,
                cwd=cwd,
                git_branch=git_branch,
                raw=entry,
            )

        elif entry_type == "system":
            subtype = entry.get("subtype", "")
            return cls(
                role="system",
                uuid=uuid,
                timestamp=timestamp,
                session_id=session_id,
                parent_uuid=parent_uuid,
                content="",
                subtype=subtype,
                cwd=cwd,
                raw=entry,
            )

        return None

    def get_text_content(self) -> str:
        """Get the text content of this turn, handling both string and block formats."""
        if isinstance(self.content, str):
            return self.content

        # Extract text from content blocks
        texts = []
        for block in self.content:
            if block.type == "text" and block.text:
                texts.append(block.text)
            elif block.type == "tool_result" and block.text:
                texts.append(f"[Tool Result]: {block.text[:200]}...")

        return "\n".join(texts)

    def get_tool_uses(self) -> list[ToolUse]:
        """Get all tool uses in this turn."""
        if isinstance(self.content, str):
            return []

        return [
            block.tool_use
            for block in self.content
            if block.type == "tool_use" and block.tool_use
        ]

    def is_user_message(self) -> bool:
        """Check if this is a user text message (not tool result)."""
        if self.role != "user":
            return False
        if isinstance(self.content, str):
            return True
        # Check if any block is a tool_result
        return not any(b.type == "tool_result" for b in self.content)


@dataclass
class Session:
    """Represents a complete Claude Code session."""

    session_id: str
    project_path: str
    file_path: Path
    turns: list[Turn] = field(default_factory=list)

    # Metadata extracted from first turn
    version: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate session duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def user_turns(self) -> list[Turn]:
        """Get only user message turns (excluding tool results)."""
        return [t for t in self.turns if t.is_user_message()]

    @property
    def assistant_turns(self) -> list[Turn]:
        """Get only assistant turns."""
        return [t for t in self.turns if t.role == "assistant"]

    def get_conversation_pairs(self) -> list[tuple[Turn, list[Turn]]]:
        """
        Get conversation as pairs of (user_turn, assistant_responses).
        Each user message may have multiple assistant responses.
        """
        pairs = []
        current_user = None
        current_responses = []

        for turn in self.turns:
            if turn.is_user_message():
                # Save previous pair if exists
                if current_user is not None:
                    pairs.append((current_user, current_responses))
                current_user = turn
                current_responses = []
            elif turn.role == "assistant":
                current_responses.append(turn)

        # Don't forget the last pair
        if current_user is not None:
            pairs.append((current_user, current_responses))

        return pairs


def parse_jsonl(file_path: Path | str) -> Generator[dict[str, Any], None, None]:
    """
    Iterate over JSON objects in a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Yields:
        Parsed JSON objects from each line

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If a line contains invalid JSON
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Session file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                # Log warning but continue parsing
                print(f"Warning: Invalid JSON at line {line_num}: {e}")
                continue


def extract_turns(file_path: Path | str) -> Session:
    """
    Parse a session JSONL file into a structured Session object.

    Args:
        file_path: Path to the JSONL session file

    Returns:
        Session object containing all parsed turns
    """
    file_path = Path(file_path)

    # Extract session ID from filename
    session_id = file_path.stem

    # Get project path from session content (reliable) or fallback to directory decode
    project_path = get_project_path_from_session(file_path)
    if project_path is None:
        # Fallback to best-effort decode of directory name
        project_dir_name = file_path.parent.name
        project_path = decode_path(project_dir_name)

    session = Session(
        session_id=session_id,
        project_path=project_path,
        file_path=file_path,
    )

    # Track tool uses to match with results
    pending_tool_uses: dict[str, ToolUse] = {}

    for entry in parse_jsonl(file_path):
        turn = Turn.from_jsonl_entry(entry)

        if turn is None:
            continue

        # Extract version from first turn
        if session.version is None:
            session.version = entry.get("version")

        # Track timestamps
        if session.start_time is None:
            session.start_time = turn.timestamp
        session.end_time = turn.timestamp

        # Track tool uses from assistant turns
        if turn.role == "assistant":
            for tool_use in turn.get_tool_uses():
                pending_tool_uses[tool_use.id] = tool_use

        # Match tool results to tool uses
        if turn.role == "user" and isinstance(turn.content, list):
            for block in turn.content:
                if block.type == "tool_result":
                    tool_id = block.raw.get("tool_use_id", "")
                    if tool_id in pending_tool_uses:
                        pending_tool_uses[tool_id].result = block.text
                        pending_tool_uses[tool_id].is_error = block.raw.get("is_error", False)

        session.turns.append(turn)

    return session


def encode_path(path: str) -> str:
    """
    Encode a filesystem path to Claude Code's directory naming convention.
    Replaces / and _ with -

    Args:
        path: Filesystem path (e.g., /mnt/c/Users/brand/Project_Workspace)

    Returns:
        Encoded path (e.g., -mnt-c-Users-brand-Project-Workspace)

    Note:
        Claude Code encodes both / and _ as -, making round-trip decoding ambiguous.
    """
    # Normalize path
    path = path.rstrip("/")
    # Replace / and _ with -
    return path.replace("/", "-").replace("_", "-")


def decode_path(encoded: str) -> str:
    """
    Attempt to decode a Claude Code directory name back to a filesystem path.

    WARNING: This is a best-effort decode. Claude Code encodes both / and _ as -,
    so the original path cannot be perfectly reconstructed. For accurate paths,
    use the cwd field from session entries.

    Args:
        encoded: Encoded directory name (e.g., -mnt-c-Users-brand)

    Returns:
        Best-effort decoded path (e.g., /mnt/c/Users/brand)
        Note: underscores will appear as slashes
    """
    if not encoded:
        return ""

    # Best effort: treat all - as /
    # This is incorrect for paths with underscores, but there's no way to know
    if encoded.startswith("-"):
        return encoded.replace("-", "/")
    return encoded


def get_project_path_from_session(file_path: Path | str) -> Optional[str]:
    """
    Extract the actual project path from a session file by reading the cwd field.

    This is the reliable way to get the original path, avoiding encoding ambiguity.

    Args:
        file_path: Path to the session JSONL file

    Returns:
        The original project path, or None if not found
    """
    file_path = Path(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    cwd = entry.get("cwd")
                    if cwd:
                        return cwd
                except json.JSONDecodeError:
                    continue
    except (OSError, IOError):
        pass

    return None


def find_current_session(
    project_path: Optional[str] = None,
    projects_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Find the most recent session file for the current or specified project.

    Args:
        project_path: Project directory path. If None, uses current working directory.
        projects_dir: Claude projects directory. If None, uses default ~/.claude/projects

    Returns:
        Path to the most recent session JSONL file, or None if not found
    """
    if projects_dir is None:
        projects_dir = CLAUDE_PROJECTS_DIR

    if project_path is None:
        project_path = os.getcwd()

    # Normalize and encode the project path
    project_path = os.path.abspath(project_path)
    encoded_project = encode_path(project_path)

    # Find the project directory
    project_dir = projects_dir / encoded_project

    if not project_dir.exists():
        # Try to find a directory that matches (in case of slight encoding differences)
        for candidate in projects_dir.iterdir():
            if candidate.is_dir():
                decoded = decode_path(candidate.name)
                if decoded == project_path or decoded.rstrip("/") == project_path.rstrip("/"):
                    project_dir = candidate
                    break
        else:
            return None

    # Find the most recent JSONL file
    jsonl_files = list(project_dir.glob("*.jsonl"))

    if not jsonl_files:
        return None

    # Sort by modification time, most recent first
    jsonl_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return jsonl_files[0]


def find_all_sessions(
    project_path: Optional[str] = None,
    projects_dir: Optional[Path] = None,
) -> list[Path]:
    """
    Find all session files for the current or specified project.

    Args:
        project_path: Project directory path. If None, uses current working directory.
        projects_dir: Claude projects directory. If None, uses default ~/.claude/projects

    Returns:
        List of session JSONL file paths, sorted by modification time (newest first)
    """
    if projects_dir is None:
        projects_dir = CLAUDE_PROJECTS_DIR

    if project_path is None:
        project_path = os.getcwd()

    # Normalize and encode the project path
    project_path = os.path.abspath(project_path)
    encoded_project = encode_path(project_path)

    # Find the project directory
    project_dir = projects_dir / encoded_project

    if not project_dir.exists():
        # Try to find a directory that matches
        for candidate in projects_dir.iterdir():
            if candidate.is_dir():
                decoded = decode_path(candidate.name)
                if decoded == project_path or decoded.rstrip("/") == project_path.rstrip("/"):
                    project_dir = candidate
                    break
        else:
            return []

    # Find all JSONL files
    jsonl_files = list(project_dir.glob("*.jsonl"))

    # Sort by modification time, most recent first
    jsonl_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return jsonl_files


def get_session_summary(session: Session) -> dict[str, Any]:
    """
    Generate a summary of a session for quick overview.

    Args:
        session: Parsed Session object

    Returns:
        Dictionary with session summary statistics
    """
    user_messages = session.user_turns
    assistant_turns = session.assistant_turns

    # Count tool uses
    all_tool_uses = []
    for turn in assistant_turns:
        all_tool_uses.extend(turn.get_tool_uses())

    # Group tool uses by name
    tool_counts: dict[str, int] = {}
    for tool_use in all_tool_uses:
        tool_counts[tool_use.name] = tool_counts.get(tool_use.name, 0) + 1

    return {
        "session_id": session.session_id,
        "project_path": session.project_path,
        "version": session.version,
        "start_time": session.start_time.isoformat() if session.start_time else None,
        "end_time": session.end_time.isoformat() if session.end_time else None,
        "duration_seconds": session.duration_seconds,
        "total_turns": len(session.turns),
        "user_messages": len(user_messages),
        "assistant_responses": len(assistant_turns),
        "tool_uses": len(all_tool_uses),
        "tools_used": tool_counts,
    }


# Module-level convenience function
def load_session(file_path: Optional[Path | str] = None) -> Session:
    """
    Load a session from a file path, or find and load the most recent session.

    Args:
        file_path: Path to session file. If None, finds the most recent session.

    Returns:
        Parsed Session object

    Raises:
        FileNotFoundError: If no session file is found
    """
    if file_path is None:
        file_path = find_current_session()
        if file_path is None:
            raise FileNotFoundError(
                "No session file found for current directory. "
                "Make sure you're in a project with Claude Code sessions."
            )

    return extract_turns(file_path)


if __name__ == "__main__":
    # Quick test/demo when run directly
    import sys

    if len(sys.argv) > 1:
        session_path = Path(sys.argv[1])
    else:
        session_path = find_current_session()

    if session_path:
        print(f"Loading session: {session_path}")
        session = extract_turns(session_path)
        summary = get_session_summary(session)

        print(f"\n{'='*60}")
        print(f"Session Summary")
        print(f"{'='*60}")
        print(f"Project: {summary['project_path']}")
        print(f"Session ID: {summary['session_id']}")
        print(f"Duration: {summary['duration_seconds']:.1f}s")
        print(f"User messages: {summary['user_messages']}")
        print(f"Assistant responses: {summary['assistant_responses']}")
        print(f"Tool uses: {summary['tool_uses']}")

        if summary['tools_used']:
            print(f"\nTools used:")
            for tool, count in sorted(summary['tools_used'].items(), key=lambda x: -x[1]):
                print(f"  {tool}: {count}")

        print(f"\n{'='*60}")
        print("Conversation Overview")
        print(f"{'='*60}")

        for user_turn, responses in session.get_conversation_pairs()[:5]:
            user_text = user_turn.get_text_content()[:100]
            print(f"\nUser: {user_text}{'...' if len(user_turn.get_text_content()) > 100 else ''}")

            for resp in responses[:2]:
                resp_text = resp.get_text_content()[:100]
                tools = resp.get_tool_uses()
                if tools:
                    print(f"  Assistant: [Used {len(tools)} tool(s): {', '.join(t.name for t in tools)}]")
                else:
                    print(f"  Assistant: {resp_text}{'...' if len(resp.get_text_content()) > 100 else ''}")
    else:
        print("No session file found for current directory.")
        print(f"Looking in: {CLAUDE_PROJECTS_DIR}")
