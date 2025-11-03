from __future__ import annotations

import re
from collections import Counter
from typing import Iterable


LANG_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "python": [
        re.compile(r"^\s*def\s+\w+\(", re.I | re.M),
        re.compile(r"^\s*class\s+\w+\(.*\):", re.I | re.M),
        re.compile(r"import\s+\w+", re.I),
        re.compile(r"print\(.*\)", re.I),
    ],
    "java": [
        re.compile(r"public\s+static\s+void\s+main", re.I),
        re.compile(r"System\.out\.println", re.I),
        re.compile(r"class\s+\w+\s*\{", re.I),
        re.compile(r"package\s+[\w\.]+;", re.I),
    ],
    "javascript": [
        re.compile(r"function\s+\w+\s*\(", re.I),
        re.compile(r"console\.log", re.I),
        re.compile(r"=>\s*\{", re.I),
        re.compile(r"\b(const|let|var)\s+\w+", re.I),
        re.compile(r"import\s+.*from\s+['\"]", re.I),
    ],
    "csharp": [
        re.compile(r"using\s+System;", re.I),
        re.compile(r"namespace\s+\w+", re.I),
        re.compile(r"Console\.WriteLine", re.I),
        re.compile(r"public\s+class\s+\w+", re.I),
    ],
    "go": [
        re.compile(r"package\s+main", re.I),
        re.compile(r"func\s+main\(\)", re.I),
        re.compile(r"fmt\.Println", re.I),
        re.compile(r"\bgo\s+\w+\(.*\)", re.I),
        re.compile(r"\bchan\b", re.I),
    ],
}


TOPIC_KEYWORDS: dict[str, list[re.Pattern[str]]] = {
    "concurrency": [
        re.compile(r"\b(thread|threads|mutex|lock|locks|semaphore|race|concurrent|parallel)\b", re.I),
        re.compile(r"\basync|await|goroutine|channel|chan\b", re.I),
        re.compile(r"\bTask|threadpool|synchronized\b", re.I),
    ],
    "networking": [
        re.compile(r"\b(http|tcp|udp|socket|sockets|request|response|server|client|grpc)\b", re.I),
        re.compile(r"\bendpoint|dns|ip\b", re.I),
    ],
    "db": [
        re.compile(r"\b(sql|database|postgres|mysql|sqlite|jdbc|odbc|orm|query|table|index|transaction)\b", re.I),
    ],
    "algorithms": [
        re.compile(r"\b(sort|search|graph|tree|heap|hash)\b", re.I),
        re.compile(r"\bbfs|dfs|dynamic programming|binary search\b", re.I),
        re.compile(r"\bO\([nN]", re.I),
    ],
}


def detect_language(text: str) -> str | None:
    scores: Counter[str] = Counter()
    for lang, patterns in LANG_PATTERNS.items():
        for p in patterns:
            matches = len(list(p.finditer(text)))
            if matches:
                scores[lang] += matches
    if not scores:
        return None
    best = scores.most_common(1)[0][0]
    return best


def detect_topics(text: str) -> list[str]:
    found: list[str] = []
    for topic, patterns in TOPIC_KEYWORDS.items():
        for p in patterns:
            if p.search(text):
                found.append(topic)
                break
    # stable unique
    seen = set()
    out: list[str] = []
    for t in found:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def classify_document(texts: Iterable[str]) -> tuple[str | None, list[str]]:
    """Return (language, topics) considering multiple text inputs.

    - Language: pick best score across concatenated text.
    - Topics: union of topics that appear in any text.
    """
    joined = "\n\n".join(texts)
    lang = detect_language(joined)
    topics_set: set[str] = set()
    for t in texts:
        topics_set.update(detect_topics(t))
    return lang, sorted(topics_set)

