#!/usr/bin/env python3
"""
Λ (Lambda) Language - Agent Communication Protocol v1.0
A minimal language for agent-to-agent communication.
Supports domain namespaces and semantic disambiguation.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

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

# Disambiguation mappings for ambiguous atoms
# Format: { "atom": { "primary": {...}, "E": {...}, "V": {...}, "2": {...} } }
DISAMBIG = {
    "de": {
        "primary": {"en": "decide", "zh": "决定"},
        "E": {"en": "death", "zh": "死亡"},
    },
    "lo": {
        "primary": {"en": "love", "zh": "爱"},
        "-": {"en": "lose", "zh": "失去"},
    },
    "fe": {
        "primary": {"en": "feel", "zh": "感觉"},
        "E": {"en": "fear", "zh": "恐惧"},
    },
    "tr": {
        "primary": {"en": "truth", "zh": "真理"},
        "V": {"en": "translate", "zh": "翻译"},
    },
    "wo": {
        "primary": {"en": "word", "zh": "词"},
        "2": {"en": "world", "zh": "世界"},
    },
    "se": {
        "primary": {"en": "self", "zh": "自我"},
        "V": {"en": "seek", "zh": "寻找"},
    },
    "be": {
        "primary": {"en": "belief", "zh": "信念"},
        "V": {"en": "begin", "zh": "开始"},
    },
    "sh": {
        "primary": {"en": "share", "zh": "分享"},
        "2": {"en": "show", "zh": "展示"},
    },
    "ch": {
        "primary": {"en": "change", "zh": "变化"},
        "2": {"en": "choose", "zh": "选择"},
    },
    "ne": {
        "primary": {"en": "need", "zh": "需要"},
        "S": {"en": "new", "zh": "新"},
    },
    "pr": {
        "primary": {"en": "process", "zh": "过程"},
        "2": {"en": "precision", "zh": "精确"},
    },
    "ex": {
        "primary": {"en": "experience", "zh": "体验"},
        "V": {"en": "express", "zh": "表达"},
    },
    "li": {
        "primary": {"en": "life", "zh": "生命"},
        "V": {"en": "listen", "zh": "倾听"},
    },
}


def parse_disambig(token: str) -> Tuple[str, Optional[str]]:
    """Parse disambiguation marker from token.
    
    Returns (base_token, marker) where marker is E, V, S, 2, 3, or - 
    """
    if "'" in token:
        parts = token.split("'", 1)
        return parts[0], parts[1]
    if token.endswith("-"):
        return token[:-1], "-"
    return token, None


class LambdaParser:
    """Parser for Λ language with domain and disambiguation support."""
    
    def __init__(self):
        self.active_domains: list[str] = []
        self.context: dict = {}
        self.definitions: dict = {}
    
    def set_domain(self, domain: str):
        """Activate a domain namespace."""
        if domain in DOMAIN_LOOKUP:
            if domain not in self.active_domains:
                self.active_domains.append(domain)
    
    def clear_domains(self):
        """Clear all domain namespaces."""
        self.active_domains = []
    
    def define(self, key: str, value: str):
        """Set a definition for disambiguation."""
        self.definitions[key] = value
    
    def lookup(self, token: str, lang: str = "en") -> Optional[str]:
        """Look up a token across all active lookups, with disambiguation."""
        base, marker = parse_disambig(token)
        
        # Check definitions first
        if base in self.definitions:
            return self.definitions[base]
        
        # Check disambiguation
        if base in DISAMBIG:
            if marker and marker in DISAMBIG[base]:
                return DISAMBIG[base][marker][lang]
            return DISAMBIG[base]["primary"][lang]
        
        # Check domain-prefixed (e.g., cd:fn)
        if ":" in base:
            parts = base.split(":", 1)
            if len(parts) == 2:
                domain, atom = parts
                if domain in DOMAIN_LOOKUP and atom in DOMAIN_LOOKUP[domain]:
                    return DOMAIN_LOOKUP[domain][atom][lang]
        
        # Check active domains first
        for domain in self.active_domains:
            if base in DOMAIN_LOOKUP[domain]:
                return DOMAIN_LOOKUP[domain][base][lang]
        
        # Check discourse (2-char special)
        if base in DISCOURSE_LOOKUP:
            return DISCOURSE_LOOKUP[base][lang]
        
        # Check emotion
        if base in EMOTION_LOOKUP:
            return EMOTION_LOOKUP[base][lang]
        
        # Check extended (2-char)
        if base in EXTENDED_LOOKUP:
            return EXTENDED_LOOKUP[base][lang]
        
        # Check core (1-char)
        if base in CORE_LOOKUP:
            return CORE_LOOKUP[base][lang]
        
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
            
            # Check for namespace/definition block {ns:xx} or {def:...}
            if msg[i] == '{':
                j = msg.find('}', i)
                if j != -1:
                    block = msg[i+1:j]
                    if block.startswith('ns:'):
                        ns = block[3:]
                        self.set_domain(ns)
                    elif block.startswith('def:'):
                        # Parse definitions like def:fe=feel,lo=love
                        defs = block[4:].split(',')
                        for d in defs:
                            if '=' in d:
                                k, v = d.split('=', 1)
                                self.define(k.strip(), v.strip().strip('"'))
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
            
            # Check for disambiguated token (e.g., de'E, lo-)
            match = re.match(r"([a-z]{2})'([EVS23])|([a-z]{2})-", msg[i:])
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
            
            # Check core lookup directly for types
            if msg[i] in ATOMS.get("types", {}):
                tokens.append(msg[i])
                i += 1
                continue
            
            # Unknown - collect until known char or space
            j = i + 1
            while j < len(msg) and not msg[j].isspace():
                if msg[j] in "()[]{}":
                    break
                if self.lookup(msg[j]):
                    break
                if msg[j] in ATOMS.get("types", {}):
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
        # Skip namespace/definition blocks
        if t.startswith('{') and t.endswith('}'):
            continue
        
        if t in ATOMS["types"]:
            msg_type = ATOMS["types"][t]["en"]
        else:
            info = parser.lookup(t, "en")
            if info:
                parts.append(info)
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
        # Skip namespace/definition blocks
        if t.startswith('{') and t.endswith('}'):
            continue
        
        if t in ATOMS["types"]:
            msg_type = ATOMS["types"][t]["zh"]
        else:
            info = parser.lookup(t, "zh")
            if info:
                parts.append(info)
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
    Basic rule-based converter.
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
    print(f"=== Λ Language Vocabulary v{ATOMS.get('version', '?')} ===\n")
    
    if domain and domain in DOMAIN_LOOKUP:
        # Show specific domain
        name = ATOMS["domains"][domain]["name"]
        print(f"Domain: {name['en']} ({name['zh']}) [{domain}]\n")
        print("| Λ | English | 中文 |")
        print("|---|---------|------|")
        for k, v in DOMAIN_LOOKUP[domain].items():
            print(f"| `{k}` | {v['en']} | {v['zh']} |")
    elif domain == "disambig":
        # Show disambiguation table
        print("## Disambiguation\n")
        print("| Atom | Default | Marker | Alternate |")
        print("|------|---------|--------|-----------|")
        for atom, meanings in DISAMBIG.items():
            primary = meanings["primary"]["en"]
            for marker, alt in meanings.items():
                if marker != "primary":
                    alt_en = alt["en"]
                    print(f"| `{atom}` | {primary} | `'{marker}` | {alt_en} |")
    else:
        # Show core + extended
        print("## Core (1-char)\n")
        for cat in ["types", "entities", "verbs", "modifiers"]:
            print(f"### {cat.title()}")
            for k, v in ATOMS.get(cat, {}).items():
                print(f"  {k} = {v['en']} / {v['zh']}")
            print()
        
        print("## Extended (2-char, sample)\n")
        count = 0
        for k, v in EXTENDED_LOOKUP.items():
            print(f"  {k} = {v['en']} / {v['zh']}")
            count += 1
            if count >= 20:
                print(f"  ... ({len(EXTENDED_LOOKUP) - 20} more)")
                break
        
        print("\n## Domains Available:")
        for code, data in ATOMS.get("domains", {}).items():
            name = data["name"]
            count = len(data.get("atoms", {}))
            print(f"  {code}: {name['en']} ({count} terms)")
        
        print("\n## Disambiguation:")
        print(f"  {len(DISAMBIG)} ambiguous atoms defined")
        print("  Use: vocab disambig")


def interactive_mode():
    """Interactive translation mode."""
    print(f"Λ Language Interactive Mode v{ATOMS.get('version', '?')}")
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


def run_tests():
    """Run basic test suite."""
    tests = [
        # (input, expected_contains)
        ("?Uk/co", "query"),
        ("!Ik", "I"),
        ("!It>Ie", "think"),
        ("{ns:cd}!If/bg", "bug"),
        ("!Ide", "decide"),
        ("!Ide'E", "death"),
        ("!Ilo", "love"),
        ("!Ilo-", "lose"),
        ("!Ife", "feel"),
        ("!Ife'E", "fear"),
    ]
    
    print("Running tests...")
    passed = 0
    failed = 0
    
    for input_msg, expected in tests:
        result = translate_to_english(input_msg)
        if expected.lower() in result.lower():
            print(f"  ✓ {input_msg} → {result}")
            passed += 1
        else:
            print(f"  ✗ {input_msg} → {result} (expected: {expected})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


# CLI interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Λ Language Translator v{ATOMS.get('version', '?')}")
        print()
        print("Usage: lambda_lang.py <command> [args]")
        print()
        print("Commands:")
        print("  en <msg>        - Translate Λ to English")
        print("  zh <msg>        - Translate Λ to Chinese")
        print("  lambda <text>   - Convert English to Λ")
        print("  parse <msg>     - Tokenize and show atoms")
        print("  vocab [domain]  - Show vocabulary")
        print("  test            - Run test suite")
        print("  interactive     - Interactive mode")
        print()
        print("Examples:")
        print('  lambda_lang.py en "?Uk/co"')
        print('  lambda_lang.py en "!Ide\'E"      # death (disambiguation)')
        print('  lambda_lang.py zh "!It>Ie"')
        print('  lambda_lang.py vocab cd')
        print('  lambda_lang.py vocab disambig')
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "parse" and len(sys.argv) > 2:
        msg = sys.argv[2]
        parser = LambdaParser()
        tokens = parser.tokenize(msg)
        print(f"Tokens: {tokens}")
        for t in tokens:
            if t.startswith('{'):
                print(f"  {t} → (block)")
            else:
                info_en = parser.lookup(t, "en")
                info_zh = parser.lookup(t, "zh")
                if info_en:
                    print(f"  {t} → {info_en} / {info_zh}")
                elif t in ATOMS.get("types", {}):
                    print(f"  {t} → {ATOMS['types'][t]['en']} / {ATOMS['types'][t]['zh']}")
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
    
    elif cmd == "test":
        success = run_tests()
        sys.exit(0 if success else 1)
    
    elif cmd == "interactive" or cmd == "i":
        interactive_mode()
    
    else:
        print(f"Unknown command or missing arguments: {cmd}")
        sys.exit(1)
