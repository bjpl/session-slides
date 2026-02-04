"""
Pytest configuration for session-slides tests.

Handles path setup and common fixtures.
"""

import sys
from pathlib import Path

import pytest


# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(scope="session")
def scripts_path():
    """Return the path to the scripts directory."""
    return SCRIPTS_DIR


@pytest.fixture
def sample_session_data():
    """Provide sample session data for testing."""
    return {
        'metadata': {
            'timestamp': '2025-02-04T10:00:00Z'
        },
        'turns': [
            {
                'prompt': 'Create a hello world function',
                'response': 'Here is a simple hello world function:\n\n```python\ndef hello():\n    return "Hello, World!"\n```',
                'tools_used': ['Write'],
                'files_modified': [{'path': 'hello.py', 'action': 'created'}]
            },
            {
                'prompt': 'Add a test for it',
                'response': 'I added a test for the hello function.',
                'tools_used': ['Write', 'Bash'],
                'files_modified': [{'path': 'test_hello.py', 'action': 'created'}]
            }
        ]
    }


@pytest.fixture
def sample_jsonl_content():
    """Provide sample JSONL content for parsing tests."""
    import json
    entries = [
        {
            "type": "user",
            "uuid": "user-001",
            "sessionId": "test-session",
            "timestamp": "2025-02-04T10:00:00Z",
            "cwd": "/test/project",
            "message": {"content": "Hello, Claude!"}
        },
        {
            "type": "assistant",
            "uuid": "asst-001",
            "parentUuid": "user-001",
            "sessionId": "test-session",
            "timestamp": "2025-02-04T10:00:01Z",
            "cwd": "/test/project",
            "message": {
                "content": [{"type": "text", "text": "Hello! How can I help you?"}]
            }
        }
    ]
    return "\n".join(json.dumps(e) for e in entries)
