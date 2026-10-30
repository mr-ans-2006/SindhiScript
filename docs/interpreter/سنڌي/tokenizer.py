# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Token Types and Token Definition

Defines the TokenType enum and Token data class used throughout
the lexer, parser, and evaluator.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class TokenType(Enum):
    """All token types for the سنڌي language."""

    # ── Literals ──────────────────────────────────────────────────
    IDENTIFIER = auto()    # User-defined names, built-in names
    NUMBER = auto()        # Integer and float literals (Arabic or Sindhi digits)
    STRING = auto()        # String literals ("..." or '...')
    FSTRING = auto()       # F-string literals (f"..." or f'...')

    # ── Reserved Words ────────────────────────────────────────────
    KEYWORD = auto()       # Language keywords (متغير, ڪم, جيڪڏهن, etc.)
    OPERATOR = auto()      # Named operators (جمع, برابر, ۽, ۾, etc.)

    # ── Punctuation / Symbols ─────────────────────────────────────
    SYMBOL = auto()        # ( ) [ ] { } : = . ،

    # ── Structural ────────────────────────────────────────────────
    NEWLINE = auto()       # End of a logical line
    INDENT = auto()        # Increase in indentation level (4 spaces)
    DEDENT = auto()        # Decrease in indentation level
    EOF = auto()           # End of source file

    # ── Special ───────────────────────────────────────────────────
    COMMENT = auto()       # Comment (# to end of line) — not emitted by default
    RAW_PYTHON = auto()    # Raw Python code body of an ٻاهري function


@dataclass
class Token:
    """
    Represents a single lexical token produced by the lexer.

    Attributes:
        type:     The classification of this token (TokenType enum).
        value:    The processed/canonical value. For numbers, this is the
                  Arabic-digit form. For operators, this is the Sindhi name.
        line:     Source line number (1-indexed).
        column:   Source column number (1-indexed, counted in Unicode
                  code points, not bytes).
        original: The original source representation, preserved when it
                  differs from `value` (e.g., Sindhi numerals ۱۲۳ vs "123").
                  None when identical to value.
    """
    type: TokenType
    value: str
    line: int
    column: int
    original: Optional[str] = None

    def __repr__(self) -> str:
        if self.original and self.original != self.value:
            return (
                f"Token({self.type.name}, {self.value!r}, "
                f"original={self.original!r}, {self.line}:{self.column})"
            )
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return self.type == other.type and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.type, self.value))

    def is_keyword(self, name: str) -> bool:
        """Check if this token is a specific keyword."""
        return self.type == TokenType.KEYWORD and self.value == name

    def is_operator(self, name: str) -> bool:
        """Check if this token is a specific operator."""
        return self.type == TokenType.OPERATOR and self.value == name

    def is_symbol(self, char: str) -> bool:
        """Check if this token is a specific symbol."""
        return self.type == TokenType.SYMBOL and self.value == char
