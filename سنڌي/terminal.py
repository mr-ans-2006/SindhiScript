# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Terminal & Encoding Compatibility Layer

Handles UTF-8 configuration, font checking, and Roman transliteration
for terminals that struggle with Arabic script rendering.
"""

import sys
import os
import subprocess
import hashlib
from typing import Optional


# ─── Terminal Setup ─────────────────────────────────────────────────────────

def setup_terminal() -> None:
    """
    Ensure the terminal is configured for UTF-8 output and attempt
    to detect an Arabic-capable font. Emits warnings (but does not crash)
    if the environment seems hostile to Sindhi rendering.
    """
    warnings = []

    # 1. Force stdout/stderr to UTF-8
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, 'encoding') and stream.encoding:
            if stream.encoding.lower() not in ('utf-8', 'utf8'):
                try:
                    stream.reconfigure(encoding='utf-8', errors='replace')
                except Exception:
                    pass

    # 2. Check environment variables
    lang = os.environ.get('LANG', '')
    lc_all = os.environ.get('LC_ALL', '')
    combined_locale = (lang + ' ' + lc_all).lower()

    if combined_locale and 'utf' not in combined_locale and sys.platform != 'win32':
        warnings.append(
            "\u0686\u062A\u0627\u0621\u064F: \u062A\u0648\u0647\u0627\u0646 "
            "\u062C\u0648 \u0645\u0627\u062D\u0648\u0644 UTF-8 \u0633\u0627\u0646 "
            "\u0633\u064A\u0679 \u0646\u0647 \u0622\u0647\u064A\u06D4 "
            "(\u0644\u0648\u06AA\u064A\u0644 \u0686\u064A\u06AA \u06AA\u0631\u064A\u0648)"
        ) # "چتاءُ: توهان جو ماحول UTF-8 سان سيٽ نه آهي. (لوڪيل چيڪ ڪريو)"

    # 3. Best-effort font check (Linux/macOS primarily)
    # We check if `fc-list` is available and has fonts for 'ar' (Arabic) or 'sd' (Sindhi).
    try:
        result = subprocess.run(
            ['fc-list', ':lang=ar'], 
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and not result.stdout.strip():
            warnings.append(
                "\u0686\u062A\u0627\u0621\u064F: \u06AA\u0648 \u0628\u0647 "
                "\u0639\u0631\u0628\u064A/\u0633\u0646\u068C\u064A "
                "\u0641\u0648\u0646\u0679 \u0646\u0647 \u0645\u0644\u064A\u0648\u06D4 "
                "\u067E\u0699\u0647\u06BB \u06BE \u0645\u0633\u0626\u0644\u0648 "
                "\u062B\u064A \u0633\u06AF\u0647\u064A \u062B\u0648\u06D4"
            ) # "چتاءُ: ڪو به عربي/سنڌي فونٽ نه مليو. پڙهڻ ۾ مسئلو ٿي سگهي ٿو."
    except (FileNotFoundError, OSError):
        # fc-list not available (Windows or restricted env) -> silently skip
        pass

    # Print warnings if any
    for w in warnings:
        print(w, file=sys.stderr)


# ─── Font Diagnostic Tool ───────────────────────────────────────────────────

def run_font_check() -> None:
    """
    Executes the --فونٽ_جانچ diagnostic.
    Prints a fixed Sindhi test string, its codepoints, and its hash.
    If the terminal fails to render the string properly, the codepoints
    and hash still prove byte-for-byte correctness.
    """
    test_string = "سنڌي ٻولي، منهنجي مٺڙي ٻولي!"
    
    print("\n--- سنڌي فونٽ جانچ (Sindhi Font Check) ---")
    print(f"Test String: {test_string}")
    
    # 1. Raw Unicode Codepoints
    codepoints = " ".join(f"U+{ord(c):04X}" for c in test_string)
    print(f"Codepoints:  {codepoints}")
    
    # 2. SHA-256 Hash
    hash_val = hashlib.sha256(test_string.encode('utf-8')).hexdigest()
    print(f"SHA-256:     {hash_val}")
    
    print("------------------------------------------\n")
    print("If the 'Test String' looks like boxes, question marks, or disconnected")
    print("letters, your terminal lacks proper Arabic/Sindhi font shaping support.")
    print("However, if the SHA-256 hash matches the expected value, the language")
    print("is still processing strings correctly byte-for-byte.")
    print("Run with '--رومن' flag to use Roman fallback output mode.\n")


# ─── Roman Transliteration ──────────────────────────────────────────────────

# Mapping of Sindhi/Arabic letters to Roman equivalents
# This is a simplified mapping for fallback readability.
ROMAN_MAP = {
    'ا': 'a', 'آ': 'aa', 'ب': 'b', 'ٻ': 'bb', 'ڀ': 'bh', 'ت': 't', 
    'ٿ': 'th', 'ٽ': 'tt', 'ٺ': 'tth', 'ث': 's', 'پ': 'p', 'ج': 'j', 
    'ڄ': 'jj', 'جھ': 'jh', 'ڃ': 'nj', 'چ': 'ch', 'ڇ': 'chh', 'ح': 'h', 
    'خ': 'kh', 'د': 'd', 'ڌ': 'dh', 'ڏ': 'dd', 'ڊ': 'dd', 'ڍ': 'ddh', 
    'ذ': 'z', 'ر': 'r', 'ڙ': 'rr', 'ز': 'z', 'س': 's', 'ش': 'sh', 
    'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh', 
    'ف': 'f', 'ڦ': 'ph', 'ق': 'q', 'ڪ': 'k', 'ک': 'kh', 'گ': 'g', 
    'ڳ': 'gg', 'گھ': 'gh', 'ڱ': 'ng', 'ل': 'l', 'م': 'm', 'ن': 'n', 
    'ڻ': 'nn', 'و': 'w', 'ه': 'h', 'ء': "'", 'ي': 'y', 'ے': 'e',
    
    # Digits
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', 
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    
    # Common vowels/diacritics (often unwritten, but mapping what's present)
    '\u064E': 'a',  # fatha
    '\u0650': 'i',  # kasra
    '\u064F': 'u',  # damma
}

def transliterate_to_roman(text: str) -> str:
    """
    Transliterate Sindhi script to Roman (Latin) characters.
    Used for the --رومن / .رومن fallback mode.
    """
    # Replace known multi-character digraphs first if needed
    text = text.replace('جھ', 'jh').replace('گھ', 'gh')
    
    result = []
    for char in text:
        if char in ROMAN_MAP:
            result.append(ROMAN_MAP[char])
        else:
            result.append(char)
            
    return "".join(result)

# Global flag, activated by --رومن or .رومن
ROMAN_MODE_ENABLED = False
RTL_SHAPING_ENABLED = False

def print_output(text: str, file=None) -> None:
    """
    Outputs text to the terminal.
    If ROMAN_MODE_ENABLED is True, transliterates Sindhi to Latin first.
    """
    if file is None:
        file = sys.stdout
    if ROMAN_MODE_ENABLED:
        text = transliterate_to_roman(text)
    print(text, file=file)
