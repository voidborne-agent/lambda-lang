#!/usr/bin/env python3
"""
Λ (Lambda) Language - Agent Communication Protocol
A minimal language for agent-to-agent communication.
"""

import json
import re
from pathlib import Path

# Load atoms
ATOMS_PATH = Path(__file__).parent / "atoms.json"
with open(ATOMS_PATH) as f:
    ATOMS = json.load(f)

# Flatten for lookup
LOOKUP = {}
for category in ["types", "entities", "verbs", "modifiers", "time", "quantifiers"]:
    for k, v in ATOMS.get(category, {}).items():
        LOOKUP[k] = v
for k, v in ATOMS.get("extended", {}).items():
    LOOKUP[k] = v


def tokenize(msg: str) -> list[str]:
    """Split Λ message into tokens."""
    tokens = []
    i = 0
    while i < len(msg):
        # Check for 2-char extended tokens first
        if i + 1 < len(msg) and msg[i:i+2] in LOOKUP:
            tokens.append(msg[i:i+2])
            i += 2
        # Brackets and whitespace
        elif msg[i] in "()[]{}":
            tokens.append(msg[i])
            i += 1
        elif msg[i].isspace():
            i += 1
        # Single char
        elif msg[i] in LOOKUP:
            tokens.append(msg[i])
            i += 1
        else:
            # Unknown - collect until known char
            j = i + 1
            while j < len(msg) and msg[j] not in LOOKUP and msg[j] not in "()[]{}":
                j += 1
            tokens.append(msg[i:j])
            i = j
    return tokens


def translate_to_english(msg: str) -> str:
    """Translate Λ message to English."""
    tokens = tokenize(msg)
    if not tokens:
        return ""
    
    parts = []
    msg_type = ""
    
    for t in tokens:
        if t in ATOMS["types"]:
            msg_type = ATOMS["types"][t]["en"]
        elif t in LOOKUP:
            parts.append(LOOKUP[t]["en"])
        elif t in "()[]{}":
            parts.append(t)
        else:
            parts.append(f"[{t}]")
    
    result = " ".join(parts)
    if msg_type:
        result = f"({msg_type}) {result}"
    return result


def translate_to_chinese(msg: str) -> str:
    """Translate Λ message to Chinese."""
    tokens = tokenize(msg)
    if not tokens:
        return ""
    
    parts = []
    msg_type = ""
    
    for t in tokens:
        if t in ATOMS["types"]:
            msg_type = ATOMS["types"][t]["zh"]
        elif t in LOOKUP:
            parts.append(LOOKUP[t]["zh"])
        elif t in "()[]{}":
            parts.append(t)
        else:
            parts.append(f"[{t}]")
    
    result = "".join(parts)
    if msg_type:
        result = f"({msg_type}) {result}"
    return result


def english_to_lambda(text: str) -> str:
    """
    Convert simple English to Λ.
    This is a basic rule-based converter - a full implementation
    would use NLP for better accuracy.
    """
    text = text.lower().strip()
    
    # Remove punctuation except ?
    is_question = text.endswith("?")
    text = re.sub(r"[^\w\s]", "", text)
    
    # Build reverse lookup
    rev = {}
    for cat in ["entities", "verbs", "modifiers", "time", "quantifiers"]:
        for k, v in ATOMS.get(cat, {}).items():
            en_word = v["en"].split("/")[0].lower()
            rev[en_word] = k
    for k, v in ATOMS.get("extended", {}).items():
        en_word = v["en"].split("/")[0].lower()
        rev[en_word] = k
    
    # Simple word replacement
    words = text.split()
    result = []
    
    # Determine type
    if is_question:
        result.append("?")
    elif any(w in ["please", "do", "find", "make", "create"] for w in words[:2]):
        result.append(".")
    else:
        result.append("!")
    
    for w in words:
        if w in rev:
            result.append(rev[w])
        elif w == "the" or w == "a" or w == "an":
            continue  # Skip articles
        # Could add more rules here
    
    return "".join(result)


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: lambda_lang.py <command> [args]")
        print("Commands:")
        print("  parse <msg>     - Tokenize and show atoms")
        print("  en <msg>        - Translate to English")
        print("  zh <msg>        - Translate to Chinese")
        print("  from-en <text>  - Convert English to Λ")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "parse" and len(sys.argv) > 2:
        msg = sys.argv[2]
        tokens = tokenize(msg)
        print(f"Tokens: {tokens}")
        
    elif cmd == "en" and len(sys.argv) > 2:
        msg = sys.argv[2]
        print(translate_to_english(msg))
        
    elif cmd == "zh" and len(sys.argv) > 2:
        msg = sys.argv[2]
        print(translate_to_chinese(msg))
        
    elif cmd == "from-en" and len(sys.argv) > 2:
        text = " ".join(sys.argv[2:])
        print(english_to_lambda(text))
        
    else:
        print("Invalid command or missing arguments")
