"""
Title Generation Module for Session Slides

Generates meaningful slide titles from user prompts using pattern matching
and verb-to-gerund transformation.

Example outputs:
    "Hey Claude, can you create a login form?" -> "Creating Login Form"
    "Please fix the authentication bug" -> "Fixing Authentication Bug"
    "Add tests for the API endpoints" -> "Adding API Endpoint Tests"
    "implement user profile feature" -> "Implementing User Profile Feature"
    "refactor the database module" -> "Refactoring Database Module"
    "Update 'config.json' with new settings" -> "Updating config.json"
    "review src/auth/login.py" -> "Reviewing src/auth/login.py"
    "optimize the search algorithm" -> "Optimizing Search Algorithm"
    "debug memory leak issue" -> "Debugging Memory Leak Issue"
    "deploy to production" -> "Deploying To Production"
    "" or unparseable -> "Turn 5"
"""

import re
from typing import Optional

# Action verbs mapped to their gerund forms
ACTION_VERBS: dict[str, str] = {
    # Creation verbs
    "create": "Creating",
    "make": "Making",
    "build": "Building",
    "generate": "Generating",
    "add": "Adding",
    "implement": "Implementing",
    "develop": "Developing",
    "design": "Designing",
    "write": "Writing",
    "setup": "Setting Up",
    "set up": "Setting Up",
    "initialize": "Initializing",
    "init": "Initializing",
    "scaffold": "Scaffolding",
    "bootstrap": "Bootstrapping",
    "establish": "Establishing",
    "introduce": "Introducing",
    "compose": "Composing",
    "construct": "Constructing",
    "craft": "Crafting",
    "draft": "Drafting",
    "formulate": "Formulating",
    "produce": "Producing",

    # Modification verbs
    "fix": "Fixing",
    "update": "Updating",
    "modify": "Modifying",
    "change": "Changing",
    "edit": "Editing",
    "revise": "Revising",
    "adjust": "Adjusting",
    "alter": "Altering",
    "amend": "Amending",
    "correct": "Correcting",
    "patch": "Patching",
    "tweak": "Tweaking",
    "enhance": "Enhancing",
    "extend": "Extending",
    "expand": "Expanding",
    "upgrade": "Upgrading",
    "improve": "Improving",

    # Refactoring verbs
    "refactor": "Refactoring",
    "restructure": "Restructuring",
    "reorganize": "Reorganizing",
    "rework": "Reworking",
    "rewrite": "Rewriting",
    "simplify": "Simplifying",
    "streamline": "Streamlining",
    "clean": "Cleaning",
    "cleanup": "Cleaning Up",
    "clean up": "Cleaning Up",
    "tidy": "Tidying",
    "modernize": "Modernizing",
    "consolidate": "Consolidating",
    "modularize": "Modularizing",
    "decouple": "Decoupling",
    "abstract": "Abstracting",
    "extract": "Extracting",
    "inline": "Inlining",
    "rename": "Renaming",
    "move": "Moving",
    "relocate": "Relocating",
    "merge": "Merging",
    "split": "Splitting",
    "separate": "Separating",

    # Removal verbs
    "remove": "Removing",
    "delete": "Deleting",
    "drop": "Dropping",
    "eliminate": "Eliminating",
    "clear": "Clearing",
    "purge": "Purging",
    "strip": "Stripping",
    "deprecate": "Deprecating",
    "disable": "Disabling",
    "uninstall": "Uninstalling",

    # Testing verbs
    "test": "Testing",
    "verify": "Verifying",
    "validate": "Validating",
    "check": "Checking",
    "assert": "Asserting",
    "ensure": "Ensuring",
    "confirm": "Confirming",
    "audit": "Auditing",
    "inspect": "Inspecting",
    "examine": "Examining",
    "analyze": "Analyzing",
    "analyse": "Analysing",
    "evaluate": "Evaluating",
    "assess": "Assessing",
    "benchmark": "Benchmarking",
    "profile": "Profiling",
    "measure": "Measuring",
    "monitor": "Monitoring",
    "trace": "Tracing",
    "lint": "Linting",

    # Debugging verbs
    "debug": "Debugging",
    "troubleshoot": "Troubleshooting",
    "diagnose": "Diagnosing",
    "investigate": "Investigating",
    "resolve": "Resolving",
    "solve": "Solving",
    "address": "Addressing",
    "handle": "Handling",
    "trace": "Tracing",
    "track": "Tracking",
    "identify": "Identifying",
    "isolate": "Isolating",
    "reproduce": "Reproducing",
    "bisect": "Bisecting",

    # Documentation verbs
    "document": "Documenting",
    "describe": "Describing",
    "explain": "Explaining",
    "comment": "Commenting",
    "annotate": "Annotating",
    "clarify": "Clarifying",
    "elaborate": "Elaborating",
    "outline": "Outlining",
    "summarize": "Summarizing",
    "detail": "Detailing",
    "specify": "Specifying",
    "define": "Defining",
    "note": "Noting",
    "record": "Recording",
    "log": "Logging",

    # Performance verbs
    "optimize": "Optimizing",
    "speed up": "Speeding Up",
    "accelerate": "Accelerating",
    "boost": "Boosting",
    "cache": "Caching",
    "parallelize": "Parallelizing",
    "async": "Making Async",
    "lazy": "Lazy Loading",
    "prefetch": "Prefetching",
    "preload": "Preloading",
    "compress": "Compressing",
    "minify": "Minifying",
    "bundle": "Bundling",
    "tree-shake": "Tree Shaking",

    # Deployment verbs
    "deploy": "Deploying",
    "release": "Releasing",
    "publish": "Publishing",
    "ship": "Shipping",
    "launch": "Launching",
    "push": "Pushing",
    "rollout": "Rolling Out",
    "roll out": "Rolling Out",
    "rollback": "Rolling Back",
    "roll back": "Rolling Back",
    "revert": "Reverting",
    "promote": "Promoting",
    "migrate": "Migrating",
    "provision": "Provisioning",
    "configure": "Configuring",
    "config": "Configuring",
    "install": "Installing",

    # Security verbs
    "secure": "Securing",
    "encrypt": "Encrypting",
    "decrypt": "Decrypting",
    "hash": "Hashing",
    "sanitize": "Sanitizing",
    "escape": "Escaping",
    "authenticate": "Authenticating",
    "authorize": "Authorizing",
    "validate": "Validating",
    "protect": "Protecting",
    "guard": "Guarding",
    "shield": "Shielding",
    "harden": "Hardening",
    "lock": "Locking",
    "restrict": "Restricting",
    "limit": "Limiting",
    "throttle": "Throttling",
    "rate-limit": "Rate Limiting",

    # Review verbs
    "review": "Reviewing",
    "approve": "Approving",
    "reject": "Rejecting",
    "accept": "Accepting",
    "request": "Requesting",
    "suggest": "Suggesting",
    "propose": "Proposing",
    "recommend": "Recommending",
    "feedback": "Providing Feedback",
    "critique": "Critiquing",

    # Integration verbs
    "integrate": "Integrating",
    "connect": "Connecting",
    "link": "Linking",
    "bind": "Binding",
    "wire": "Wiring",
    "hook": "Hooking",
    "attach": "Attaching",
    "join": "Joining",
    "combine": "Combining",
    "unify": "Unifying",
    "sync": "Syncing",
    "synchronize": "Synchronizing",
    "import": "Importing",
    "export": "Exporting",
    "load": "Loading",
    "fetch": "Fetching",
    "pull": "Pulling",
    "get": "Getting",
    "retrieve": "Retrieving",
    "query": "Querying",
    "search": "Searching",
    "find": "Finding",
    "lookup": "Looking Up",
    "look up": "Looking Up",

    # Data verbs
    "save": "Saving",
    "store": "Storing",
    "persist": "Persisting",
    "serialize": "Serializing",
    "deserialize": "Deserializing",
    "parse": "Parsing",
    "format": "Formatting",
    "transform": "Transforming",
    "convert": "Converting",
    "map": "Mapping",
    "reduce": "Reducing",
    "filter": "Filtering",
    "sort": "Sorting",
    "group": "Grouping",
    "aggregate": "Aggregating",
    "normalize": "Normalizing",
    "denormalize": "Denormalizing",
    "flatten": "Flattening",
    "nest": "Nesting",
    "index": "Indexing",

    # UI verbs
    "render": "Rendering",
    "display": "Displaying",
    "show": "Showing",
    "hide": "Hiding",
    "toggle": "Toggling",
    "animate": "Animating",
    "transition": "Transitioning",
    "style": "Styling",
    "theme": "Theming",
    "layout": "Laying Out",
    "position": "Positioning",
    "align": "Aligning",
    "center": "Centering",
    "resize": "Resizing",
    "scale": "Scaling",
    "scroll": "Scrolling",
    "paginate": "Paginating",
    "virtualize": "Virtualizing",

    # Lifecycle verbs
    "start": "Starting",
    "stop": "Stopping",
    "restart": "Restarting",
    "pause": "Pausing",
    "resume": "Resuming",
    "suspend": "Suspending",
    "terminate": "Terminating",
    "kill": "Killing",
    "spawn": "Spawning",
    "fork": "Forking",
    "clone": "Cloning",
    "copy": "Copying",
    "duplicate": "Duplicating",
    "backup": "Backing Up",
    "restore": "Restoring",
    "recover": "Recovering",
    "reset": "Resetting",
    "initialize": "Initializing",
    "finalize": "Finalizing",
    "cleanup": "Cleaning Up",
    "teardown": "Tearing Down",
    "destroy": "Destroying",

    # Communication verbs
    "send": "Sending",
    "receive": "Receiving",
    "broadcast": "Broadcasting",
    "emit": "Emitting",
    "listen": "Listening",
    "subscribe": "Subscribing",
    "unsubscribe": "Unsubscribing",
    "publish": "Publishing",
    "notify": "Notifying",
    "alert": "Alerting",
    "warn": "Warning",
    "report": "Reporting",
    "ping": "Pinging",
    "poll": "Polling",
    "stream": "Streaming",
    "pipe": "Piping",
    "route": "Routing",
    "redirect": "Redirecting",
    "forward": "Forwarding",
    "proxy": "Proxying",

    # General action verbs
    "run": "Running",
    "execute": "Executing",
    "invoke": "Invoking",
    "call": "Calling",
    "trigger": "Triggering",
    "fire": "Firing",
    "dispatch": "Dispatching",
    "schedule": "Scheduling",
    "queue": "Queueing",
    "process": "Processing",
    "compute": "Computing",
    "calculate": "Calculating",
    "determine": "Determining",
    "decide": "Deciding",
    "select": "Selecting",
    "choose": "Choosing",
    "pick": "Picking",
    "use": "Using",
    "apply": "Applying",
    "enable": "Enabling",
    "activate": "Activating",
    "deactivate": "Deactivating",
    "set": "Setting",
    "unset": "Unsetting",
    "assign": "Assigning",
    "allocate": "Allocating",
    "deallocate": "Deallocating",
    "free": "Freeing",
    "release": "Releasing",
    "acquire": "Acquiring",
    "obtain": "Obtaining",
    "register": "Registering",
    "unregister": "Unregistering",
    "mount": "Mounting",
    "unmount": "Unmounting",
    "wrap": "Wrapping",
    "unwrap": "Unwrapping",
    "pack": "Packing",
    "unpack": "Unpacking",
    "encode": "Encoding",
    "decode": "Decoding",
    "compile": "Compiling",
    "transpile": "Transpiling",
    "interpret": "Interpreting",
    "evaluate": "Evaluating",
    "exec": "Executing",
}

# Common prefixes to strip from prompts
COMMON_PREFIXES = [
    # Polite requests
    r"^hey\s+claude[,.]?\s*",
    r"^hi\s+claude[,.]?\s*",
    r"^hello\s+claude[,.]?\s*",
    r"^dear\s+claude[,.]?\s*",
    r"^claude[,.]?\s*",

    # Request phrases
    r"^can\s+you\s+(please\s+)?",
    r"^could\s+you\s+(please\s+)?",
    r"^would\s+you\s+(please\s+)?",
    r"^will\s+you\s+(please\s+)?",
    r"^please\s+(can\s+you\s+)?",
    r"^i\s+need\s+you\s+to\s+",
    r"^i\s+want\s+you\s+to\s+",
    r"^i\'?d\s+like\s+you\s+to\s+",
    r"^i\s+would\s+like\s+you\s+to\s+",
    r"^help\s+me\s+(to\s+)?",
    r"^let\'?s\s+",
    r"^go\s+ahead\s+and\s+",
    r"^now\s+",
    r"^next[,.]?\s+",
    r"^then[,.]?\s+",
    r"^also[,.]?\s+",
    r"^additionally[,.]?\s+",
    r"^furthermore[,.]?\s+",
    r"^moreover[,.]?\s+",

    # Filler words
    r"^okay[,.]?\s*",
    r"^ok[,.]?\s*",
    r"^so[,.]?\s*",
    r"^well[,.]?\s*",
    r"^alright[,.]?\s*",
    r"^right[,.]?\s*",
    r"^sure[,.]?\s*",
    r"^yeah[,.]?\s*",
    r"^yes[,.]?\s*",
    r"^um+[,.]?\s*",
    r"^uh+[,.]?\s*",
    r"^hmm+[,.]?\s*",
    r"^just\s+",
    r"^quickly\s+",
    r"^simply\s+",
    r"^basically\s+",
]

# Patterns that indicate the start of a prompt is technical noise (errors, logs, etc.)
TECHNICAL_NOISE_PATTERNS = [
    r"^(?:Unchecked|Error|Warning|Failed|Exception|TypeError|SyntaxError|ReferenceError)",
    r"^(?:runtime\.|console\.|window\.)",
    r"^(?:\[[\w\s]+\])",  # [ERROR], [WARN], [INFO], etc.
    r"^(?:\d{4}-\d{2}-\d{2})",  # Date-formatted logs
    r"^(?:at\s+\w+\s*\()",  # Stack trace lines
    r"^(?:GET|POST|PUT|DELETE|PATCH)\s+/",  # HTTP methods
    r"^(?:\d{3}\s+)",  # HTTP status codes
    r"^(?:npm|yarn|pnpm)\s+(?:ERR|WARN)",  # Package manager errors
    r"^(?:\.{3})",  # Continuation dots
]

# File path pattern
FILE_PATH_PATTERN = re.compile(
    r"""
    (?:^|[\s'"(])                      # Start or whitespace/quote/paren
    (
        (?:\.{0,2}/)?                  # Optional ./ or ../
        (?:[\w.-]+/)*                  # Directory path components
        [\w.-]+                        # Filename
        \.[\w]+                        # Extension
    )
    (?:$|[\s'")])                      # End or whitespace/quote/paren
    """,
    re.VERBOSE
)

# Quoted string pattern
QUOTED_STRING_PATTERN = re.compile(
    r"""
    ['""`]                             # Opening quote
    ([^'"`]+?)                         # Content (non-greedy)
    ['""`]                             # Closing quote
    """,
    re.VERBOSE
)

# Feature/component phrase patterns
FEATURE_PATTERNS = [
    r"(?:the\s+)?(\w+(?:\s+\w+)*?)\s+(?:feature|functionality|capability|module|component|service|system|api|endpoint|route|page|view|screen|form|button|modal|dialog|panel|widget|controller|handler|middleware|hook|util|helper|function|method|class|interface|type|model|schema|migration|seed|fixture|test|spec|config|setting|option|parameter|argument|variable|constant|enum|flag|toggle|switch)",
    r"(?:the\s+)?(\w+(?:\s+\w+)*?)\s+(?:bug|issue|error|problem|defect|regression|glitch|flaw)",
    r"(?:the\s+)?(\w+(?:\s+\w+)*?)\s+(?:logic|algorithm|implementation|behavior|behaviour|flow|process|workflow|pipeline|chain)",
    r"(?:a\s+)?new\s+(\w+(?:\s+\w+)*)",
    r"(?:the\s+)?(\w+)\s+(?:to|for|in|on|at|with)\s+",
]

# Words to exclude from subject extraction
STOP_WORDS = {
    "a", "an", "the", "this", "that", "these", "those",
    "i", "you", "we", "they", "he", "she", "it",
    "my", "your", "our", "their", "his", "her", "its",
    "me", "us", "them", "him",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "will", "would", "could", "should", "may", "might", "must", "shall",
    "can", "need", "want",
    "and", "or", "but", "nor", "so", "yet", "for",
    "in", "on", "at", "to", "of", "from", "by", "with", "as",
    "into", "onto", "upon", "out", "up", "down", "off", "over", "under",
    "through", "between", "among", "within", "without", "about", "after",
    "before", "during", "since", "until", "unless", "while", "although",
    "if", "when", "where", "how", "why", "what", "which", "who", "whom",
    "some", "any", "all", "most", "many", "much", "few", "several",
    "each", "every", "either", "neither", "both", "other", "another",
    "such", "same", "different", "various", "certain",
    "first", "second", "third", "last", "next", "previous",
    "new", "old", "good", "bad", "best", "worst", "better", "worse",
    "big", "small", "large", "little", "great", "long", "short",
    "high", "low", "top", "bottom", "left", "right", "front", "back",
    "more", "less", "very", "too", "enough", "quite", "rather", "really",
    "just", "only", "even", "still", "already", "always", "never", "often",
    "sometimes", "usually", "also", "again", "now", "then", "here", "there",
    "please", "thanks", "thank", "sorry", "okay", "ok", "yes", "no",
    "maybe", "perhaps", "probably", "possibly", "certainly", "definitely",
    "actually", "basically", "essentially", "simply", "mainly", "mostly",
    "especially", "particularly", "specifically", "generally", "typically",
    "however", "therefore", "thus", "hence", "consequently", "accordingly",
    "furthermore", "moreover", "additionally", "besides", "meanwhile",
    "instead", "otherwise", "nevertheless", "nonetheless", "regardless",
}


def _is_technical_noise(text: str) -> bool:
    """
    Check if text starts with technical noise (error messages, logs, etc.).

    Args:
        text: The text to check

    Returns:
        True if the text appears to be technical noise
    """
    for pattern in TECHNICAL_NOISE_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False


def _find_meaningful_sentence(text: str) -> str | None:
    """
    Find the first meaningful sentence in a prompt that starts with technical noise.

    Looks for sentences containing action verbs or clear user requests.

    Args:
        text: The full prompt text

    Returns:
        A meaningful sentence or None
    """
    # Split by common sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 5:
            continue

        # Skip sentences that look like technical noise
        if _is_technical_noise(sentence):
            continue

        # Skip sentences that are just paths or URLs
        if sentence.startswith('/') or sentence.startswith('http'):
            continue

        # Look for sentences with action verbs or request phrases
        sentence_lower = sentence.lower()
        for verb in ACTION_VERBS:
            if verb in sentence_lower:
                return sentence

        # Look for request indicators
        if any(phrase in sentence_lower for phrase in ['please', 'can you', 'need to', 'want to', 'help me', 'should', 'fix', 'update', 'create', 'review']):
            return sentence

    return None


def _clean_prompt(prompt: str) -> str:
    """
    Remove common prefixes and clean up the prompt for title extraction.

    If the prompt starts with technical noise (errors, logs), tries to find
    a meaningful sentence later in the prompt.

    Args:
        prompt: The raw user prompt

    Returns:
        Cleaned prompt with prefixes removed
    """
    cleaned = prompt.strip()

    # If starts with technical noise, try to find a meaningful part
    if _is_technical_noise(cleaned):
        meaningful = _find_meaningful_sentence(cleaned)
        if meaningful:
            cleaned = meaningful
        else:
            # No meaningful part found - extract any actionable text
            # Look for common request patterns anywhere in the text
            patterns = [
                r'(?:please|can you|need to|want to|help me)\s+(.+?)(?:\.|$)',
                r'(?:fix|update|create|add|implement|review|check)\s+(.+?)(?:\.|$)',
            ]
            for pattern in patterns:
                match = re.search(pattern, cleaned, re.IGNORECASE)
                if match:
                    # Return the whole matched segment including the verb
                    start = match.start()
                    cleaned = cleaned[start:match.end()].strip()
                    break

    # Apply prefix removal patterns iteratively
    for pattern in COMMON_PREFIXES:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove leading/trailing punctuation and whitespace
    cleaned = cleaned.strip(" \t\n\r.,;:!?-")

    return cleaned


def _find_action_verb(text: str) -> tuple[str | None, str]:
    """
    Find the first action verb in the text and return its gerund form.

    Args:
        text: The cleaned prompt text

    Returns:
        Tuple of (gerund form or None, remaining text after verb)
    """
    text_lower = text.lower()
    words = text_lower.split()

    if not words:
        return None, text

    # Check for two-word verb phrases first (e.g., "set up", "clean up")
    if len(words) >= 2:
        two_word = f"{words[0]} {words[1]}"
        if two_word in ACTION_VERBS:
            remaining = " ".join(text.split()[2:])
            return ACTION_VERBS[two_word], remaining

    # Check single word verb
    first_word = words[0]
    if first_word in ACTION_VERBS:
        remaining = " ".join(text.split()[1:])
        return ACTION_VERBS[first_word], remaining

    return None, text


def _extract_quoted_string(text: str) -> str | None:
    """
    Extract the first quoted string from the text.

    Args:
        text: The text to search

    Returns:
        The quoted content or None
    """
    match = QUOTED_STRING_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def _extract_file_path(text: str) -> str | None:
    """
    Extract a file path from the text.

    Args:
        text: The text to search

    Returns:
        The file path or None
    """
    match = FILE_PATH_PATTERN.search(text)
    if match:
        path = match.group(1).strip()
        # Validate it looks like a real path
        if "/" in path or "." in path:
            return path
    return None


def _extract_feature_phrase(text: str) -> str | None:
    """
    Extract a feature or component phrase from the text.

    Args:
        text: The text to search

    Returns:
        The feature phrase or None
    """
    for pattern in FEATURE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            phrase = match.group(1).strip()
            # Filter out stop words only phrases
            words = phrase.lower().split()
            if any(w not in STOP_WORDS for w in words):
                return phrase
    return None


def _extract_meaningful_nouns(text: str, max_words: int = 4) -> str | None:
    """
    Extract meaningful nouns/noun phrases from the text.

    Args:
        text: The text to search
        max_words: Maximum number of words to include

    Returns:
        The noun phrase or None
    """
    # Remove common articles and prepositions at the start
    text = re.sub(r"^(the|a|an|some|any)\s+", "", text, flags=re.IGNORECASE)

    words = text.split()
    meaningful_words = []

    for word in words:
        # Clean the word
        clean_word = re.sub(r"[^\w\-.]", "", word)
        if not clean_word:
            continue

        # Skip stop words unless we have context
        if clean_word.lower() in STOP_WORDS and not meaningful_words:
            continue

        # Stop at prepositions/conjunctions after collecting some words
        if clean_word.lower() in {"to", "for", "in", "on", "at", "with", "by", "from", "and", "or"}:
            if meaningful_words:
                break
            continue

        meaningful_words.append(clean_word)

        if len(meaningful_words) >= max_words:
            break

    if meaningful_words:
        return " ".join(meaningful_words)
    return None


def _title_case(text: str) -> str:
    """
    Convert text to title case, preserving file paths and technical terms.

    Args:
        text: The text to convert

    Returns:
        Title-cased text
    """
    # If it looks like a file path, preserve it
    if "/" in text or (text.startswith(".") and "." in text[1:]):
        return text

    words = text.split()
    result = []

    for i, word in enumerate(words):
        # Preserve file paths within phrases
        if "/" in word or (word.startswith(".") and "." in word[1:]):
            result.append(word)
        # Preserve acronyms (all caps)
        elif word.isupper() and len(word) > 1:
            result.append(word)
        # Preserve camelCase and PascalCase
        elif any(c.isupper() for c in word[1:]):
            result.append(word)
        # Lowercase small words in middle of title
        elif i > 0 and word.lower() in {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}:
            result.append(word.lower())
        else:
            result.append(word.capitalize())

    return " ".join(result)


def generate_turn_title(prompt: str, turn_number: int) -> str:
    """
    Generate a meaningful title from a user prompt.

    The function uses a priority-based extraction approach:
    1. Clean common prefixes (hey claude, can you, please, etc.)
    2. Find action verb and map to gerund form
    3. Extract subject using priority order:
       a. Quoted strings (explicit naming)
       b. File paths (specific targets)
       c. Feature phrases (semantic patterns)
       d. Meaningful nouns (fallback extraction)
    4. Combine into "Action Subject" format
    5. Fallback to "Turn N" if nothing meaningful

    Args:
        prompt: The user's prompt text
        turn_number: The turn number for fallback title

    Returns:
        A descriptive title string

    Examples:
        >>> generate_turn_title("Hey Claude, can you create a login form?", 1)
        'Creating Login Form'

        >>> generate_turn_title("Please fix the authentication bug", 2)
        'Fixing Authentication Bug'

        >>> generate_turn_title("Add tests for the API endpoints", 3)
        'Adding API Endpoint Tests'

        >>> generate_turn_title("implement user profile feature", 4)
        'Implementing User Profile Feature'

        >>> generate_turn_title("refactor the database module", 5)
        'Refactoring Database Module'

        >>> generate_turn_title("Update 'config.json' with new settings", 6)
        'Updating config.json'

        >>> generate_turn_title("review src/auth/login.py", 7)
        'Reviewing src/auth/login.py'

        >>> generate_turn_title("optimize the search algorithm", 8)
        'Optimizing Search Algorithm'

        >>> generate_turn_title("debug memory leak issue", 9)
        'Debugging Memory Leak Issue'

        >>> generate_turn_title("deploy to production", 10)
        'Deploying To Production'

        >>> generate_turn_title("", 11)
        'Turn 11'

        >>> generate_turn_title("asdfghjkl", 12)
        'Turn 12'
    """
    fallback = f"Turn {turn_number}"

    if not prompt or not prompt.strip():
        return fallback

    # Step 1: Clean the prompt
    cleaned = _clean_prompt(prompt)
    if not cleaned:
        return fallback

    # Step 2: Find action verb
    gerund, remaining = _find_action_verb(cleaned)

    # Step 3: Extract subject (priority order)
    subject = None

    # 3a: Try quoted strings first (highest priority - explicit naming)
    subject = _extract_quoted_string(cleaned)

    # 3b: Try file paths (second priority - specific targets)
    if not subject:
        subject = _extract_file_path(remaining if gerund else cleaned)

    # 3c: Try feature phrases (third priority - semantic patterns)
    if not subject:
        subject = _extract_feature_phrase(remaining if gerund else cleaned)

    # 3d: Try meaningful nouns (fallback)
    if not subject:
        subject = _extract_meaningful_nouns(remaining if gerund else cleaned)

    # Step 4: Combine title
    if gerund and subject:
        return f"{gerund} {_title_case(subject)}"
    elif gerund:
        # Have verb but no subject - use remaining text if reasonable
        if remaining and len(remaining) > 2:
            return f"{gerund} {_title_case(remaining[:50])}"
        return f"{gerund}"
    elif subject:
        # Have subject but no verb - use subject as title
        return _title_case(subject)

    # Step 5: Fallback
    return fallback


def generate_continued_title(base_title: str) -> str:
    """
    Generate a continuation title from a base title.

    Args:
        base_title: The original title

    Returns:
        The title with "(continued)" appended

    Examples:
        >>> generate_continued_title("Creating Login Form")
        'Creating Login Form (continued)'

        >>> generate_continued_title("Turn 5")
        'Turn 5 (continued)'

        >>> generate_continued_title("Fixing Authentication Bug (continued)")
        'Fixing Authentication Bug (continued)'
    """
    if not base_title:
        return "(continued)"

    # Don't double-add continued
    if base_title.endswith("(continued)"):
        return base_title

    return f"{base_title} (continued)"


def generate_title_ollama(
    prompt: str,
    turn_number: int,
    model: str = "llama3.2",
    host: str = "http://localhost:11434",
    timeout: float = 5.0
) -> str:
    """
    Generate a title using Ollama for AI-enhanced extraction.

    Falls back to pattern-based generation if Ollama is unavailable.

    Args:
        prompt: The user's prompt text
        turn_number: The turn number for fallback
        model: The Ollama model to use
        host: The Ollama API host
        timeout: Request timeout in seconds

    Returns:
        An AI-generated or pattern-based title

    Examples:
        >>> # With Ollama running:
        >>> generate_title_ollama("Can you help me create a REST API with authentication?", 1)
        'Creating REST API Authentication'

        >>> # Without Ollama (falls back to pattern matching):
        >>> generate_title_ollama("fix the broken login", 2)
        'Fixing Broken Login'
    """
    # Try Ollama first
    try:
        import requests

        system_prompt = """You are a title generator. Given a user's request, generate a short (2-5 word)
        descriptive title in gerund form (e.g., "Creating Login Form", "Fixing Database Bug").

        Rules:
        - Start with a gerund (verb ending in -ing)
        - Keep it concise and specific
        - Use title case
        - Do not include punctuation
        - Output ONLY the title, nothing else"""

        response = requests.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": f"Generate a title for this request: {prompt}",
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 20,
                }
            },
            timeout=timeout
        )

        if response.status_code == 200:
            result = response.json()
            title = result.get("response", "").strip()

            # Validate the title
            if title and 2 <= len(title.split()) <= 6:
                # Clean up any quotes or extra punctuation
                title = title.strip("\"'.,;:!?")
                return title

    except Exception:
        # Ollama not available or error - fall through to pattern matching
        pass

    # Fallback to pattern-based generation
    return generate_turn_title(prompt, turn_number)


# Module-level convenience for testing
if __name__ == "__main__":
    # Test examples
    test_prompts = [
        ("Hey Claude, can you create a login form?", 1),
        ("Please fix the authentication bug", 2),
        ("Add tests for the API endpoints", 3),
        ("implement user profile feature", 4),
        ("refactor the database module", 5),
        ("Update 'config.json' with new settings", 6),
        ("review src/auth/login.py", 7),
        ("optimize the search algorithm", 8),
        ("debug memory leak issue", 9),
        ("deploy to production", 10),
        ("", 11),
        ("asdfghjkl", 12),
        ("Could you please help me set up the testing framework?", 13),
        ("I need you to analyze the performance bottlenecks", 14),
        ("Let's clean up the deprecated code", 15),
    ]

    print("Title Generation Examples:")
    print("-" * 60)
    for prompt, turn in test_prompts:
        title = generate_turn_title(prompt, turn)
        print(f"Prompt: {prompt[:50]!r}...")
        print(f"Title:  {title}")
        print()

    print("\nContinued Titles:")
    print("-" * 60)
    print(generate_continued_title("Creating Login Form"))
    print(generate_continued_title("Turn 5"))
