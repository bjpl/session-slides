"""
Integration tests for session-slides package.

Tests data format compatibility, truncation behavior, round-trip conversion,
and edge cases.

Run with: pytest scripts/tests/test_integration.py -v
"""

import json
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest


# ============================================================================
# SAMPLE TEST DATA
# ============================================================================

SAMPLE_JSONL_ENTRIES = [
    # System init message
    {
        "type": "system",
        "subtype": "init",
        "uuid": "sys-001",
        "sessionId": "test-session-123",
        "timestamp": "2025-02-04T10:00:00Z",
        "cwd": "/test/project",
        "version": "1.0.0"
    },
    # User message (simple text)
    {
        "type": "user",
        "uuid": "user-001",
        "parentUuid": "sys-001",
        "sessionId": "test-session-123",
        "timestamp": "2025-02-04T10:00:01Z",
        "cwd": "/test/project",
        "message": {
            "content": "Create a simple hello world function"
        }
    },
    # Assistant response with tool use
    {
        "type": "assistant",
        "uuid": "asst-001",
        "parentUuid": "user-001",
        "sessionId": "test-session-123",
        "timestamp": "2025-02-04T10:00:02Z",
        "cwd": "/test/project",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": "I'll create a hello world function for you.\n\n```python\ndef hello_world():\n    return \"Hello, World!\"\n```"
                },
                {
                    "type": "tool_use",
                    "id": "tool-001",
                    "name": "Write",
                    "input": {
                        "file_path": "/test/project/hello.py",
                        "content": "def hello_world():\n    return \"Hello, World!\"\n"
                    }
                }
            ],
            "model": "claude-sonnet-4-20250514"
        }
    },
    # Tool result (user message with tool_result content)
    {
        "type": "user",
        "uuid": "user-002",
        "parentUuid": "asst-001",
        "sessionId": "test-session-123",
        "timestamp": "2025-02-04T10:00:03Z",
        "cwd": "/test/project",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool-001",
                    "content": "File written successfully"
                }
            ]
        }
    },
    # Second user message
    {
        "type": "user",
        "uuid": "user-003",
        "parentUuid": "user-002",
        "sessionId": "test-session-123",
        "timestamp": "2025-02-04T10:00:04Z",
        "cwd": "/test/project",
        "message": {
            "content": "Add a test for this function"
        }
    },
    # Second assistant response
    {
        "type": "assistant",
        "uuid": "asst-002",
        "parentUuid": "user-003",
        "sessionId": "test-session-123",
        "timestamp": "2025-02-04T10:00:05Z",
        "cwd": "/test/project",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": "I'll add a test for the hello world function."
                },
                {
                    "type": "tool_use",
                    "id": "tool-002",
                    "name": "Write",
                    "input": {
                        "file_path": "/test/project/test_hello.py",
                        "content": "def test_hello():\n    assert hello_world() == 'Hello, World!'\n"
                    }
                },
                {
                    "type": "tool_use",
                    "id": "tool-003",
                    "name": "Bash",
                    "input": {
                        "command": "pytest test_hello.py -v",
                        "description": "Run the test"
                    }
                }
            ],
            "model": "claude-sonnet-4-20250514"
        }
    }
]


def create_test_jsonl(entries: list[dict]) -> str:
    """Create JSONL content from list of entries."""
    return "\n".join(json.dumps(e) for e in entries)


def write_temp_jsonl(entries: list[dict]) -> Path:
    """Write entries to a temporary JSONL file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(create_test_jsonl(entries))
        return Path(f.name)


# ============================================================================
# TEST: DATA FORMAT COMPATIBILITY
# ============================================================================

class TestDataFormatCompatibility:
    """
    Verify session_to_dict output matches what generate_html expects.

    The session_to_dict function combines user prompts with assistant responses
    into "conversation turns" with this format:
        {number, prompt, response, tools_used, files_modified, title, timestamp}
    """

    @pytest.fixture
    def session_file(self, tmp_path):
        """Create a temporary session file."""
        jsonl_file = tmp_path / "test-session.jsonl"
        jsonl_file.write_text(create_test_jsonl(SAMPLE_JSONL_ENTRIES))
        return jsonl_file

    def test_turn_has_required_fields(self, session_file):
        """Each turn should have: prompt, response, tools_used, files_modified."""
        import sys
        sys.path.insert(0, str(session_file.parent.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict

        session = extract_turns(session_file)
        session_dict = session_to_dict(session)

        assert 'turns' in session_dict
        assert len(session_dict['turns']) > 0

        # Check each turn has the expected fields for html_generator
        for turn in session_dict['turns']:
            assert 'number' in turn, "Turn missing 'number'"
            assert 'prompt' in turn, "Turn missing 'prompt'"
            assert 'response' in turn, "Turn missing 'response'"
            assert 'tools_used' in turn, "Turn missing 'tools_used'"
            assert 'files_modified' in turn, "Turn missing 'files_modified'"
            assert 'title' in turn, "Turn missing 'title'"

    def test_tools_used_is_list_of_strings(self, session_file):
        """tools_used should be a list of formatted tool descriptions."""
        import sys
        sys.path.insert(0, str(session_file.parent.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict

        session = extract_turns(session_file)
        session_dict = session_to_dict(session)

        for turn in session_dict['turns']:
            tools = turn.get('tools_used', [])
            assert isinstance(tools, list)
            for tool in tools:
                assert isinstance(tool, str), f"Tool should be string, got {type(tool)}"

    def test_files_modified_has_path_and_action(self, session_file):
        """files_modified entries should have path and action."""
        import sys
        sys.path.insert(0, str(session_file.parent.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict

        session = extract_turns(session_file)
        session_dict = session_to_dict(session)

        for turn in session_dict['turns']:
            for file_info in turn.get('files_modified', []):
                assert 'path' in file_info, "File info missing 'path'"
                assert 'action' in file_info, "File info missing 'action'"
                assert file_info['action'] in ('created', 'modified', 'deleted')

    def test_session_metadata(self, session_file):
        """Session dict should include metadata."""
        import sys
        sys.path.insert(0, str(session_file.parent.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict

        session = extract_turns(session_file)
        session_dict = session_to_dict(session)

        assert 'session_id' in session_dict
        assert 'project_path' in session_dict
        assert 'total_turns' in session_dict
        assert 'metadata' in session_dict


# ============================================================================
# TEST: TRUNCATION BEHAVIOR
# ============================================================================

class TestTruncation:
    """Verify truncation is applied correctly."""

    def test_long_prompt_truncated(self):
        """Long prompts should be truncated with '...'."""
        from truncation import truncate_user_prompt, TruncationConfig

        config = TruncationConfig(prompt_max_chars=50)
        long_prompt = "This is a very long prompt that exceeds the maximum character limit by a significant amount."

        result = truncate_user_prompt(long_prompt, config)

        assert len(result) <= 55  # Allow small buffer for ellipsis
        assert result.endswith("...")

    def test_short_prompt_unchanged(self):
        """Short prompts should remain unchanged."""
        from truncation import truncate_user_prompt, TruncationConfig

        config = TruncationConfig(prompt_max_chars=100)
        short_prompt = "Fix the bug"

        result = truncate_user_prompt(short_prompt, config)

        assert result == short_prompt

    def test_code_block_short_unchanged(self):
        """Code blocks under threshold should be unchanged."""
        from truncation import truncate_code_block, TruncationConfig

        config = TruncationConfig(code_short_threshold=15)
        short_code = "\n".join([f"line {i}" for i in range(10)])

        result = truncate_code_block(short_code, "python", config)

        assert result == short_code.rstrip()

    def test_code_block_medium_truncated(self):
        """Code blocks between thresholds show head + omitted + tail."""
        from truncation import truncate_code_block, TruncationConfig

        config = TruncationConfig(
            code_short_threshold=10,
            code_long_threshold=50,
            code_head_lines=3,
            code_tail_lines=2
        )
        medium_code = "\n".join([f"line {i}: code here" for i in range(25)])

        result = truncate_code_block(medium_code, "python", config)

        assert "lines omitted" in result
        assert "line 0" in result  # Head preserved
        assert "line 24" in result  # Tail preserved

    def test_code_block_over_40_lines_summary(self):
        """Code blocks over 40 lines should show summary only."""
        from truncation import truncate_code_block, TruncationConfig

        config = TruncationConfig(code_long_threshold=40)
        long_code = "\n".join([f"line {i}: implementation details" for i in range(100)])

        result = truncate_code_block(long_code, "typescript", config)

        assert "100 lines" in result
        assert "truncated" in result.lower()

    def test_terminal_output_preserves_errors(self):
        """Terminal output should preserve error lines."""
        from truncation import truncate_terminal_output, TruncationConfig

        config = TruncationConfig(terminal_max_lines=3, terminal_include_errors=True)
        terminal = """Line 1: Starting process
Line 2: Loading modules
Line 3: Initializing
Line 4: Processing data
Line 5: Error: Connection failed
Line 6: More output
Line 7: Warning: Deprecated function"""

        result = truncate_terminal_output(terminal, config)

        # First 3 lines should be present
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        # Error lines should be preserved
        assert "Error: Connection failed" in result
        assert "Warning: Deprecated function" in result

    def test_list_truncation_with_count(self):
        """Lists should truncate with 'and N more'."""
        from truncation import truncate_list, TruncationConfig

        config = TruncationConfig(list_max_items=3)
        items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"]

        result = truncate_list(items, config)

        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result
        assert "Item 4" not in result
        assert "and 3 more" in result


# ============================================================================
# TEST: ROUND-TRIP CONVERSION
# ============================================================================

class TestRoundTrip:
    """Test Parse JSONL -> session_to_dict -> generate_html -> valid HTML."""

    @pytest.fixture
    def session_file(self, tmp_path):
        """Create a temporary session file."""
        jsonl_file = tmp_path / "test-session.jsonl"
        jsonl_file.write_text(create_test_jsonl(SAMPLE_JSONL_ENTRIES))
        return jsonl_file

    def test_round_trip_produces_valid_html(self, session_file):
        """Full pipeline should produce valid HTML."""
        import sys
        sys.path.insert(0, str(session_file.parent.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict
        from html_generator import generate_html

        # Parse JSONL
        session = extract_turns(session_file)
        assert session is not None

        # Convert to dict
        session_dict = session_to_dict(session)
        assert session_dict is not None

        # Generate HTML
        html = generate_html(session_dict, title="Test Session")

        # Verify HTML structure
        assert html.startswith("<!DOCTYPE html>")
        assert "<html" in html
        assert "</html>" in html
        assert "<title>Test Session</title>" in html

    def test_html_contains_slide_content(self, session_file):
        """Generated HTML should contain slide content."""
        import sys
        sys.path.insert(0, str(session_file.parent.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict
        from html_generator import generate_html

        session = extract_turns(session_file)
        session_dict = session_to_dict(session)
        html = generate_html(session_dict, title="Test Session")

        # Should contain slide structure
        assert 'class="slide"' in html
        assert 'class="navigation"' in html

        # Should contain user prompt text (escaped)
        assert "hello world" in html.lower()

    def test_html_has_navigation_elements(self, session_file):
        """Generated HTML should have navigation controls."""
        import sys
        sys.path.insert(0, str(session_file.parent.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict
        from html_generator import generate_html

        session = extract_turns(session_file)
        session_dict = session_to_dict(session)
        html = generate_html(session_dict, title="Test Session")

        # Check navigation elements
        assert "prevSlide" in html or "prev-btn" in html
        assert "nextSlide" in html or "next-btn" in html
        assert "progress" in html.lower()


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_session(self, tmp_path):
        """Empty session should be handled gracefully."""
        import sys
        sys.path.insert(0, str(tmp_path.parent / "scripts"))

        from parser import extract_turns

        # Create empty JSONL file
        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("")

        session = extract_turns(empty_file)
        assert session.turns == []

    def test_session_with_only_system_messages(self, tmp_path):
        """Session with only system messages should produce empty turns."""
        import sys
        sys.path.insert(0, str(tmp_path.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict

        system_only = [
            {
                "type": "system",
                "subtype": "init",
                "uuid": "sys-001",
                "sessionId": "test-session",
                "timestamp": "2025-02-04T10:00:00Z",
                "cwd": "/test"
            },
            {
                "type": "system",
                "subtype": "progress",
                "uuid": "sys-002",
                "sessionId": "test-session",
                "timestamp": "2025-02-04T10:00:01Z",
                "cwd": "/test"
            }
        ]

        jsonl_file = tmp_path / "system-only.jsonl"
        jsonl_file.write_text(create_test_jsonl(system_only))

        session = extract_turns(jsonl_file)

        # System turns should be tracked but not as user messages
        user_turns = [t for t in session.turns if t.is_user_message()]
        assert len(user_turns) == 0

    def test_very_long_code_blocks(self):
        """Code blocks with 100+ lines should be heavily truncated."""
        from truncation import truncate_code_block, TruncationConfig

        config = TruncationConfig(code_long_threshold=40)
        very_long_code = "\n".join([
            f"line {i}: {'x' * 80}" for i in range(150)
        ])

        result = truncate_code_block(very_long_code, "python", config)

        # Should be heavily summarized
        assert "150 lines" in result
        assert len(result) < len(very_long_code) / 2

    def test_unicode_content(self, tmp_path):
        """Unicode content should be handled correctly."""
        import sys
        sys.path.insert(0, str(tmp_path.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict
        from html_generator import generate_html

        unicode_entries = [
            {
                "type": "user",
                "uuid": "user-001",
                "sessionId": "test-session",
                "timestamp": "2025-02-04T10:00:00Z",
                "cwd": "/test",
                "message": {
                    "content": "Create a function that returns 'Hello, World!' in Japanese"
                }
            },
            {
                "type": "assistant",
                "uuid": "asst-001",
                "parentUuid": "user-001",
                "sessionId": "test-session",
                "timestamp": "2025-02-04T10:00:01Z",
                "cwd": "/test",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Here's the function with Japanese greeting:\n\n```python\ndef greet():\n    return 'Konnichiwa'\n```"
                        }
                    ]
                }
            }
        ]

        jsonl_file = tmp_path / "unicode.jsonl"
        jsonl_file.write_text(create_test_jsonl(unicode_entries), encoding='utf-8')

        session = extract_turns(jsonl_file)
        session_dict = session_to_dict(session)
        html = generate_html(session_dict, title="Unicode Test")

        # Unicode should be properly encoded in HTML
        assert "<!DOCTYPE html>" in html
        # Content should be present (may be HTML-escaped)
        assert "Japanese" in html or "&#" in html

    def test_code_block_without_language(self, tmp_path):
        """Code blocks without language specifier should be handled."""
        import sys
        sys.path.insert(0, str(tmp_path.parent / "scripts"))

        from html_generator import format_response_content

        content = """Here's some code:

```
function test() {
    return true;
}
```

That's it."""

        result = format_response_content(content)

        # Should still create code block
        assert 'class="code-block"' in result
        assert "function test()" in result

    def test_nested_code_blocks_in_response(self):
        """Multiple code blocks in a response should all be formatted."""
        from html_generator import format_response_content

        content = """First code block:

```python
def foo():
    pass
```

Second code block:

```javascript
const bar = () => {};
```

End of response."""

        result = format_response_content(content)

        # Both code blocks should be present
        assert result.count('class="code-block"') == 2
        assert "def foo" in result
        assert "const bar" in result

    def test_inline_code_escaping(self):
        """Inline code should be properly escaped."""
        from html_generator import format_response_content

        content = "Use `<script>alert('xss')</script>` to test XSS."

        result = format_response_content(content)

        # Script tags should be escaped
        assert "<script>" not in result
        assert "&lt;script&gt;" in result or "alert" in result

    def test_special_html_characters_escaped(self):
        """Special HTML characters in content should be escaped."""
        from html_generator import format_response_content

        content = "Use <div> and & characters in HTML. Also test \"quotes\"."

        result = format_response_content(content)

        # HTML should be escaped
        assert "&lt;div&gt;" in result
        assert "&amp;" in result

    def test_empty_tool_input(self, tmp_path):
        """Tools with empty input should be handled."""
        import sys
        sys.path.insert(0, str(tmp_path.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict

        entries = [
            {
                "type": "user",
                "uuid": "user-001",
                "sessionId": "test-session",
                "timestamp": "2025-02-04T10:00:00Z",
                "cwd": "/test",
                "message": {"content": "Test request"}
            },
            {
                "type": "assistant",
                "uuid": "asst-001",
                "parentUuid": "user-001",
                "sessionId": "test-session",
                "timestamp": "2025-02-04T10:00:01Z",
                "cwd": "/test",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Running custom tool"
                        },
                        {
                            "type": "tool_use",
                            "id": "tool-001",
                            "name": "CustomTool",
                            "input": {}
                        }
                    ]
                }
            }
        ]

        jsonl_file = tmp_path / "empty-input.jsonl"
        jsonl_file.write_text(create_test_jsonl(entries))

        session = extract_turns(jsonl_file)
        session_dict = session_to_dict(session)

        # Should not crash and should have 1 conversation turn
        assert session_dict is not None
        assert len(session_dict['turns']) == 1

        # The turn should have the tool in tools_used
        turn = session_dict['turns'][0]
        assert 'tools_used' in turn
        assert len(turn['tools_used']) == 1
        assert 'Customtool' in turn['tools_used'][0] or 'CustomTool' in turn['tools_used'][0]

    def test_assistant_only_response(self, tmp_path):
        """Assistant message without preceding user message should not crash."""
        import sys
        sys.path.insert(0, str(tmp_path.parent / "scripts"))

        from parser import extract_turns
        from generate_slides import session_to_dict

        # Edge case: assistant turn without user turn
        entries = [
            {
                "type": "assistant",
                "uuid": "asst-001",
                "sessionId": "test-session",
                "timestamp": "2025-02-04T10:00:00Z",
                "cwd": "/test",
                "message": {
                    "content": [{"type": "text", "text": "Hello!"}]
                }
            }
        ]

        jsonl_file = tmp_path / "orphan-assistant.jsonl"
        jsonl_file.write_text(create_test_jsonl(entries))

        session = extract_turns(jsonl_file)
        session_dict = session_to_dict(session)

        # Should handle gracefully - no conversation pairs without user turns
        assert session_dict is not None
        assert 'turns' in session_dict


# ============================================================================
# TEST: TITLE GENERATION
# ============================================================================

class TestTitleGeneration:
    """Test title generation from prompts."""

    def test_action_verb_to_gerund(self):
        """Action verbs should be converted to gerund form."""
        from titles import generate_turn_title

        test_cases = [
            ("Create a login form", "Creating"),
            ("Fix the bug", "Fixing"),
            ("Add tests", "Adding"),
            ("Update config", "Updating"),
            ("Refactor the module", "Refactoring"),
        ]

        for prompt, expected_start in test_cases:
            title = generate_turn_title(prompt, 1)
            assert title.startswith(expected_start), f"'{prompt}' -> '{title}' should start with '{expected_start}'"

    def test_empty_prompt_fallback(self):
        """Empty prompts should use fallback title."""
        from titles import generate_turn_title

        assert generate_turn_title("", 5) == "Turn 5"
        assert generate_turn_title("   ", 10) == "Turn 10"

    def test_prefix_stripping(self):
        """Common prefixes should be stripped."""
        from titles import generate_turn_title

        test_cases = [
            "Hey Claude, create a form",
            "Can you please create a form",
            "Please create a form",
            "I need you to create a form",
        ]

        for prompt in test_cases:
            title = generate_turn_title(prompt, 1)
            assert "hey" not in title.lower()
            assert "please" not in title.lower()
            assert "can you" not in title.lower()


# ============================================================================
# TEST: HTML GENERATOR SPECIFICS
# ============================================================================

class TestHtmlGenerator:
    """Test HTML generator specific functionality."""

    def test_generate_html_with_empty_turns(self):
        """generate_html should handle session with no turns."""
        from html_generator import generate_html

        empty_session = {
            'metadata': {},
            'turns': []
        }

        html = generate_html(empty_session, title="Empty Session")

        assert "<!DOCTYPE html>" in html
        assert "Empty Session" in html

    def test_tool_badges_rendered(self):
        """Tool badges should be rendered in HTML."""
        from html_generator import generate_html

        session = {
            'metadata': {},
            'turns': [
                {
                    'prompt': 'Test prompt',
                    'response': 'Test response',
                    'tools_used': ['Read', 'Write', 'Bash'],
                    'files_modified': []
                }
            ]
        }

        html = generate_html(session, title="Tool Test")

        assert 'class="tool-badge"' in html
        assert 'Read' in html
        assert 'Write' in html
        assert 'Bash' in html

    def test_files_modified_rendered(self):
        """Files modified should be rendered in HTML."""
        from html_generator import generate_html

        session = {
            'metadata': {},
            'turns': [
                {
                    'prompt': 'Test prompt',
                    'response': 'Test response',
                    'tools_used': [],
                    'files_modified': [
                        {'path': 'src/main.py', 'action': 'created'},
                        {'path': 'tests/test_main.py', 'action': 'modified'}
                    ]
                }
            ]
        }

        html = generate_html(session, title="Files Test")

        assert 'src/main.py' in html
        assert 'tests/test_main.py' in html
        assert 'created' in html
        assert 'modified' in html


# ============================================================================
# TEST: PARSER SPECIFICS
# ============================================================================

class TestParser:
    """Test parser specific functionality."""

    def test_path_encoding(self):
        """Path encoding should replace / and _ with -."""
        from parser import encode_path

        assert encode_path("/mnt/c/Users/test") == "-mnt-c-Users-test"
        assert encode_path("/home/user/my_project") == "-home-user-my-project"

    def test_tool_use_description(self):
        """ToolUse should generate descriptions."""
        from parser import ToolUse

        bash_tool = ToolUse(
            id="1",
            name="Bash",
            input={"command": "npm install"}
        )
        assert "npm install" in bash_tool.get_description()

        read_tool = ToolUse(
            id="2",
            name="Read",
            input={"file_path": "/path/to/file.py"}
        )
        assert "file.py" in read_tool.get_description()

    def test_turn_get_text_content(self, tmp_path):
        """Turn.get_text_content should extract text from various formats."""
        import sys
        sys.path.insert(0, str(tmp_path.parent / "scripts"))

        from parser import Turn, ContentBlock
        from datetime import datetime

        # Test with string content
        turn1 = Turn(
            role="user",
            uuid="1",
            timestamp=datetime.now(),
            session_id="test",
            content="Simple text content"
        )
        assert turn1.get_text_content() == "Simple text content"

        # Test with content blocks
        turn2 = Turn(
            role="assistant",
            uuid="2",
            timestamp=datetime.now(),
            session_id="test",
            content=[
                ContentBlock(type="text", text="First block"),
                ContentBlock(type="text", text="Second block")
            ]
        )
        text = turn2.get_text_content()
        assert "First block" in text
        assert "Second block" in text


# ============================================================================
# TEST: TOOL FORMATTING
# ============================================================================

class TestToolFormatting:
    """Test tool use formatting."""

    def test_format_tool_use_read(self):
        """Read tool should show filename."""
        from truncation import format_tool_use

        result = format_tool_use("Read", {"file_path": "/path/to/config.json"})
        assert "config.json" in result
        assert "Reading" in result

    def test_format_tool_use_write(self):
        """Write tool should show filename."""
        from truncation import format_tool_use

        result = format_tool_use("Write", {"file_path": "/src/main.py"})
        assert "main.py" in result
        assert "Writing" in result

    def test_format_tool_use_bash(self):
        """Bash tool should show command."""
        from truncation import format_tool_use

        result = format_tool_use("Bash", {"command": "npm install"})
        assert "npm install" in result
        assert "Running" in result

    def test_format_tool_use_long_command_truncated(self):
        """Long bash commands should be truncated."""
        from truncation import format_tool_use

        long_cmd = "npm install --save-dev typescript @types/node eslint prettier jest"
        result = format_tool_use("Bash", {"command": long_cmd})

        assert len(result) < len(long_cmd) + 20
        assert "..." in result or len(result) <= 60


# ============================================================================
# RUN CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
