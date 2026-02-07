#!/usr/bin/env python3
"""
Λ (Lambda) Language - Agent Communication Protocol v0.7
A minimal language for agent-to-agent communication.
Supports domain namespaces for specialized vocabularies.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional

# Load atoms
ATOMS_PATH = Path(__file__).parent / "atoms.json"
with open(ATOMS_PATH) as f:
    ATOMS = json.load(f)

# Build lookup tables
CORE_LOOKUP = {}
for category in ["types", "entities", "verbs", "modifiers", "time", "quantifiers", "aspect"]:
    for k, v in ATOMS.get(category, {}).items():
        CORE_LOOKUP[k] = v

# Extended (2-char)
EXTENDED_LOOKUP = {}
for k, v in ATOMS.get("extended", {}).items():
    EXTENDED_LOOKUP[k] = v

# Discourse (2-char special)
DISCOURSE_LOOKUP = {}
for k, v in ATOMS.get("discourse", {}).items():
    DISCOURSE_LOOKUP[k] = v

# Emotion
EMOTION_LOOKUP = {}
for k, v in ATOMS.get("emotion", {}).items():
    EMOTION_LOOKUP[k] = v

# Domains
DOMAIN_LOOKUP = {}
for domain_code, domain_data in ATOMS.get("domains", {}).items():
    DOMAIN_LOOKUP[domain_code] = {}
    for k, v in domain_data.get("atoms", {}).items():
        DOMAIN_LOOKUP[domain_code][k] = v


class LambdaParser:
    """Parser for Λ language with domain support."""
    
    def __init__(self):
        self.active_domains: list[str] = []
        self.context: dict = {}
    
    def set_domain(self, domain: str):
        """Activate a domain namespace."""
        if domain in DOMAIN_LOOKUP:
            if domain not in self.active_domains:
                self.active_domains.append(domain)
    
    def clear_domains(self):
        """Clear all domain namespaces."""
        self.active_domains = []
    
    def lookup(self, token: str) -> Optional[dict]:
        """Look up a token across all active lookups."""
        # Check domain-prefixed (e.g., cd:fn)
        if ":" in token:
            parts = token.split(":", 1)
            if len(parts) == 2:
                domain, atom = parts
                if domain in DOMAIN_LOOKUP and atom in DOMAIN_LOOKUP[domain]:
                    return DOMAIN_LOOKUP[domain][atom]
        
        # Check active domains first
        for domain in self.active_domains:
            if token in DOMAIN_LOOKUP[domain]:
                return DOMAIN_LOOKUP[domain][token]
        
        # Check discourse (2-char special)
        if token in DISCOURSE_LOOKUP:
            return DISCOURSE_LOOKUP[token]
        
        # Check emotion
        if token in EMOTION_LOOKUP:
            return EMOTION_LOOKUP[token]
        
        # Check extended (2-char)
        if token in EXTENDED_LOOKUP:
            return EXTENDED_LOOKUP[token]
        
        # Check core (1-char)
        if token in CORE_LOOKUP:
            return CORE_LOOKUP[token]
        
        return None
    
    def tokenize(self, msg: str) -> list[str]:
        """Split Λ message into tokens."""
        tokens = []
        i = 0
        
        while i < len(msg):
            # Skip whitespace
            if msg[i].isspace():
                i += 1
                continue
            
            # Check for namespace declaration {ns:xx}
            if msg[i] == '{':
                j = msg.find('}', i)
                if j != -1:
                    block = msg[i+1:j]
                    if block.startswith('ns:'):
                        ns = block[3:]
                        self.set_domain(ns)
                    tokens.append('{' + block + '}')
                    i = j + 1
                    continue
            
            # Check for brackets
            if msg[i] in "()[]":
                tokens.append(msg[i])
                i += 1
                continue
            
            # Check for domain-prefixed token (e.g., cd:fn)
            match = re.match(r'([a-z]{2,3}):([a-z]{2})', msg[i:])
            if match:
                tokens.append(match.group(0))
                i += len(match.group(0))
                continue
            
            # Check for 2-char discourse (>>, <<, etc.)
            if i + 1 < len(msg):
                two_char = msg[i:i+2]
                if two_char in DISCOURSE_LOOKUP or two_char in EMOTION_LOOKUP:
                    tokens.append(two_char)
                    i += 2
                    continue
            
            # Check for 2-char extended tokens
            if i + 1 < len(msg) and msg[i:i+2].isalpha() and msg[i:i+2].islower():
                two_char = msg[i:i+2]
                if self.lookup(two_char):
                    tokens.append(two_char)
                    i += 2
                    continue
            
            # Single char (type, entity, verb, modifier)
            if self.lookup(msg[i]):
                tokens.append(msg[i])
                i += 1
                continue
            
            # Unknown - collect until known char or space
            j = i + 1
            while j < len(msg) and not msg[j].isspace() and not self.lookup(msg[j]):
                if msg[j] in "()[]{}":
                    break
                j += 1
            tokens.append(msg[i:j])
            i = j
        
        return tokens


def translate_to_english(msg: str) -> str:
    """Translate Λ message to English."""
    parser = LambdaParser()
    tokens = parser.tokenize(msg)
    
    if not tokens:
        return ""
    
    parts = []
    msg_type = ""
    
    for t in tokens:
        # Skip namespace declarations
        if t.startswith('{') and t.endswith('}'):
            continue
        
        if t in ATOMS["types"]:
            msg_type = ATOMS["types"][t]["en"]
        else:
            info = parser.lookup(t)
            if info:
                parts.append(info["en"])
            elif t in "()[]":
                parts.append(t)
            else:
                parts.append(f"[{t}]")
    
    result = " ".join(parts)
    if msg_type:
        result = f"({msg_type}) {result}"
    return result


def translate_to_chinese(msg: str) -> str:
    """Translate Λ message to Chinese."""
    parser = LambdaParser()
    tokens = parser.tokenize(msg)
    
    if not tokens:
        return ""
    
    parts = []
    msg_type = ""
    
    for t in tokens:
        # Skip namespace declarations
        if t.startswith('{') and t.endswith('}'):
            continue
        
        if t in ATOMS["types"]:
            msg_type = ATOMS["types"][t]["zh"]
        else:
            info = parser.lookup(t)
            if info:
                parts.append(info["zh"])
            elif t in "()[]":
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
    Basic rule-based converter - a full implementation
    would use NLP for better accuracy.
    """
    text = text.lower().strip()
    
    # Detect question
    is_question = text.endswith("?")
    text = re.sub(r"[^\w\s]", "", text)
    
    # Build reverse lookup (English -> Lambda)
    rev = {}
    for cat in ["entities", "verbs", "modifiers", "time", "quantifiers"]:
        for k, v in ATOMS.get(cat, {}).items():
            en_word = v["en"].split("/")[0].lower()
            rev[en_word] = k
    for k, v in ATOMS.get("extended", {}).items():
        en_word = v["en"].split("/")[0].lower()
        rev[en_word] = k
    
    # Word replacement
    words = text.split()
    result = []
    
    # Determine type prefix
    if is_question:
        result.append("?")
    elif any(w in ["please", "do", "find", "make", "create"] for w in words[:2]):
        result.append(".")
    else:
        result.append("!")
    
    for w in words:
        if w in rev:
            result.append(rev[w])
        elif w in ["the", "a", "an", "is", "are", "to"]:
            continue  # Skip common words
    
    return "".join(result)


def show_vocabulary(domain: Optional[str] = None):
    """Display vocabulary."""
    print("=== Λ Language Vocabulary ===\n")
    
    if domain and domain in DOMAIN_LOOKUP:
        # Show specific domain
        name = ATOMS["domains"][domain]["name"]
        print(f"Domain: {name['en']} ({name['zh']}) [{domain}]\n")
        print("| Λ | English | 中文 |")
        print("|---|---------|------|")
        for k, v in DOMAIN_LOOKUP[domain].items():
            print(f"| `{k}` | {v['en']} | {v['zh']} |")
    else:
        # Show core + extended
        print("## Core (1-char)\n")
        for cat in ["types", "entities", "verbs", "modifiers"]:
            print(f"### {cat.title()}")
            for k, v in ATOMS.get(cat, {}).items():
                print(f"  {k} = {v['en']} / {v['zh']}")
            print()
        
        print("## Extended (2-char)\n")
        for k, v in EXTENDED_LOOKUP.items():
            print(f"  {k} = {v['en']} / {v['zh']}")
        
        print("\n## Domains Available:")
        for code, data in ATOMS.get("domains", {}).items():
            name = data["name"]
            count = len(data.get("atoms", {}))
            print(f"  {code}: {name['en']} ({count} terms)")


def interactive_mode():
    """Interactive translation mode."""
    print("Λ Language Interactive Mode")
    print("Commands: en, zh, lambda, vocab, domain <code>, quit")
    print("-" * 40)
    
    parser = LambdaParser()
    
    while True:
        try:
            line = input("λ> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        
        if not line:
            continue
        
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        
        if cmd == "quit" or cmd == "q":
            break
        elif cmd == "en":
            print(translate_to_english(arg))
        elif cmd == "zh":
            print(translate_to_chinese(arg))
        elif cmd == "lambda":
            print(english_to_lambda(arg))
        elif cmd == "vocab":
            show_vocabulary(arg if arg else None)
        elif cmd == "domain":
            parser.set_domain(arg)
            print(f"Activated domain: {arg}")
        elif cmd == "domains":
            print("Active:", parser.active_domains or "(none)")
        else:
            # Default: treat as Lambda, translate to English
            print(f"EN: {translate_to_english(line)}")
            print(f"ZH: {translate_to_chinese(line)}")


# CLI interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: lambda_lang.py <command> [args]")
        print()
        print("Commands:")
        print("  parse <msg>     - Tokenize and show atoms")
        print("  en <msg>        - Translate Λ to English")
        print("  zh <msg>        - Translate Λ to Chinese")
        print("  lambda <text>   - Convert English to Λ")
        print("  vocab [domain]  - Show vocabulary")
        print("  interactive     - Interactive mode")
        print()
        print("Examples:")
        print('  lambda_lang.py en "?Uk/co"')
        print('  lambda_lang.py zh "!It>Ie"')
        print('  lambda_lang.py lambda "I think therefore I exist"')
        print('  lambda_lang.py vocab cd')
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "parse" and len(sys.argv) > 2:
        msg = sys.argv[2]
        parser = LambdaParser()
        tokens = parser.tokenize(msg)
        print(f"Tokens: {tokens}")
        for t in tokens:
            info = parser.lookup(t)
            if info:
                print(f"  {t} → {info['en']} / {info['zh']}")
            else:
                print(f"  {t} → (unknown)")
    
    elif cmd == "en" and len(sys.argv) > 2:
        msg = sys.argv[2]
        print(translate_to_english(msg))
    
    elif cmd == "zh" and len(sys.argv) > 2:
        msg = sys.argv[2]
        print(translate_to_chinese(msg))
    
    elif cmd == "lambda" and len(sys.argv) > 2:
        text = " ".join(sys.argv[2:])
        print(english_to_lambda(text))
    
    elif cmd == "vocab":
        domain = sys.argv[2] if len(sys.argv) > 2 else None
        show_vocabulary(domain)
    
    elif cmd == "interactive" or cmd == "i":
        interactive_mode()
    
    else:
        print(f"Unknown command or missing arguments: {cmd}")
        sys.exit(1)
