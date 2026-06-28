# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Lexer

Converts source text into a stream of Token objects. Handles:
  • UTF-8 encoding (all files read with encoding='utf-8')
  • Sindhi/Arabic script identifiers and keywords
  • Dual numeral support: Arabic (0-9) and Sindhi (۰-۹)
  • String literals with escape sequences and f-strings
  • Indentation-based block structure (4 spaces per level, tabs are errors)
  • 16 named operators (14 word-based + 2 single-char: ۽ ۾)
  • FFI raw-capture mode for ٻاهري function bodies
  • Line/column tracking in Unicode code points (not bytes)
  • Naming rule enforcement (no operator tokens inside identifiers)

Unicode Coverage (verified programmatically — see verify_unicode.py):
  All 45 unique characters from the Phase 0 approved table fall within
  U+0600–U+06FF (Arabic block). All 17 Sindhi-specific letters (ٻ ٽ ٺ
  پ ڀ ڄ ڃ ڇ ڊ ڍ ڌ ڏ ڙ ڦ ڪ ڳ ڻ) have Unicode category Lo (Letter,
  other). The two Sindhi symbol operators (۽ U+06FD, ۾ U+06FE) have
  category So (Symbol, other) and are excluded from identifier chars.
  Sindhi digits ۰-۹ (U+06F0–U+06F9) have category Nd (Number, decimal).
"""

import unicodedata
from typing import List, Optional

from .tokenizer import TokenType, Token


# ═════════════════════════════════════════════════════════════════════
# CONSTANTS — Keywords, Operators, Character Classes
# ═════════════════════════════════════════════════════════════════════

# ─── Keywords (27 reserved words from approved Phase 0 table) ─────

KEYWORDS = frozenset({
    # Declarations
    'متغير',       # let
    'ثابت',        # const
    'ڪم',          # function
    'طبقو',        # class
    'ورثو',        # inherits

    # Control flow
    'جيڪڏهن',      # if
    'نه_ته',       # else
    'ٻي_صورت',     # elif
    'هر',          # for
    'جڏهن_تائين',   # while
    'ٽوڙيو',       # break
    'جاري',        # continue
    'موٽايو',      # return

    # Exception handling
    'ڪوشش',        # try
    'غلطي',        # except
    'آخر',         # finally

    # Literal values
    'صحيح',        # true
    'غلط',         # false
    'ڪجهه_نه',     # null/None

    # Module system
    'آندو',        # import
    'مان',         # from
    'جاريات',      # export

    # OOP
    'پنهنجو',      # self
    'نئون',        # new

    # FFI
    'ٻاهري',       # extern/native
})


# ─── Word Operators (14 word-based operators) ────────────────────

WORD_OPERATORS = {
    'جمع':          '+',     # addition
    'گهٽائڻ':       '-',     # subtraction
    'ضرب':          '*',     # multiplication
    'تقسيم':        '/',     # division
    'باقي':         '%',     # modulo
    'طاقت':         '**',    # exponentiation
    'وڌيڪ':         '>',     # greater than
    'گهٽ':          '<',     # less than
    'برابر':        '==',    # equals
    'نه_برابر':     '!=',    # not equals
    'وڌيڪ_برابر':   '>=',    # greater-or-equal
    'گهٽ_برابر':    '<=',    # less-or-equal
    'يا':           'or',    # logical or
    'نه':           'not',   # logical not
}

# ─── Single-Character Operators (2 Sindhi-specific symbols) ───────

SINGLE_CHAR_OPERATORS = {
    '\u06FD': 'and',   # ۽ — ARABIC SIGN SINDHI AMPERSAND
    '\u06FE': 'in',    # ۾ — ARABIC SIGN SINDHI POSTPOSITION MEN
}

# Set of all operator names for quick lookup
ALL_OPERATOR_WORDS = frozenset(WORD_OPERATORS.keys())


# ─── Numeral Conversion Tables ───────────────────────────────────

SINDHI_TO_ARABIC = str.maketrans(
    '\u06F0\u06F1\u06F2\u06F3\u06F4\u06F5\u06F6\u06F7\u06F8\u06F9',
    '0123456789'
)

# ─── String Escape Sequences ─────────────────────────────────────

ESCAPE_MAP = {
    'n':  '\n',
    't':  '\t',
    '\\': '\\',
    '"':  '"',
    "'":  "'",
}

# ─── Symbol Characters ───────────────────────────────────────────
# () [] {} for grouping/collections, : for blocks, = for assignment,
# . for attribute access, ، (U+060C Arabic comma) for separators

SYMBOLS = frozenset('()[]{}:=.\u060C')


# ═════════════════════════════════════════════════════════════════════
# CHARACTER CLASSIFICATION HELPERS
# ═════════════════════════════════════════════════════════════════════

def is_sindhi_letter(ch: str) -> bool:
    """
    Check if a character is a valid Sindhi/Arabic letter for identifiers.

    Accepts characters from the Arabic Unicode blocks with category L*
    (Letter). Excludes symbols (like ۽ ۾), marks, and digits.

    Ranges checked:
      U+0600–U+06FF  Arabic (covers all Sindhi-specific letters)
      U+0750–U+077F  Arabic Supplement (included for safety)
      U+08A0–U+08FF  Arabic Extended-A
      U+FB50–U+FDFF  Arabic Presentation Forms-A
      U+FE70–U+FEFF  Arabic Presentation Forms-B
    """
    cp = ord(ch)
    if not (
        (0x0600 <= cp <= 0x06FF) or
        (0x0750 <= cp <= 0x077F) or
        (0x08A0 <= cp <= 0x08FF) or
        (0xFB50 <= cp <= 0xFDFF) or
        (0xFE70 <= cp <= 0xFEFF)
    ):
        return False
    return unicodedata.category(ch).startswith('L')


def is_sindhi_digit(ch: str) -> bool:
    """Check if character is a Sindhi/Extended Arabic-Indic digit (۰-۹)."""
    return '\u06F0' <= ch <= '\u06F9'


def is_arabic_digit(ch: str) -> bool:
    """Check if character is a Western Arabic digit (0-9)."""
    return '0' <= ch <= '9'


def is_any_digit(ch: str) -> bool:
    """Check if character is any accepted digit (Western or Sindhi)."""
    return is_arabic_digit(ch) or is_sindhi_digit(ch)


def is_identifier_start(ch: str) -> bool:
    """Check if character can start an identifier (Sindhi letter or _)."""
    return is_sindhi_letter(ch) or ch == '_' or ch in ('\u200C', '\u200D')


def is_identifier_char(ch: str) -> bool:
    """Check if character can appear in an identifier body."""
    return is_sindhi_letter(ch) or is_any_digit(ch) or ch == '_' or ch in ('\u200C', '\u200D')


def sindhi_to_arabic(text: str) -> str:
    """Convert Sindhi numerals in text to Western Arabic digits."""
    return text.translate(SINDHI_TO_ARABIC)


# ═════════════════════════════════════════════════════════════════════
# UNICODE RANGE VERIFICATION (runs at import time)
# ═════════════════════════════════════════════════════════════════════

def _verify_phase0_unicode():
    """
    Verify that every letter in the Phase 0 approved keyword/operator
    table falls inside our accepted Unicode ranges with category L*.

    This fulfills the Phase 1 spec requirement for programmatic
    verification. Raises RuntimeError on failure.
    """
    all_tokens = list(KEYWORDS) + list(WORD_OPERATORS.keys())
    unique_chars = set()
    for token in all_tokens:
        for ch in token:
            if ch != '_':
                unique_chars.add(ch)

    for ch in unique_chars:
        cp = ord(ch)
        cat = unicodedata.category(ch)

        # ۽ and ۾ are symbol operators (So), not identifier letters — OK
        if ch in SINGLE_CHAR_OPERATORS:
            continue

        if not is_sindhi_letter(ch):
            raise RuntimeError(
                f"Phase 0 Unicode verification failed: "
                f"U+{cp:04X} '{ch}' ({unicodedata.name(ch, '?')}) "
                f"has category {cat} and is not recognized as a Sindhi letter"
            )

from .errors import RuntimeError

_verify_phase0_unicode()


from .errors import LexerError


# ═════════════════════════════════════════════════════════════════════
# LEXER
# ═════════════════════════════════════════════════════════════════════

class Lexer:
    """
    Lexer for the سنڌي programming language.

    Converts a source string into a list of Token objects.
    Handles indentation-based blocks, Sindhi/Arabic script,
    bidirectional numeral support, and FFI raw-capture mode.

    Usage:
        lexer = Lexer(source_code, filename='example.سن')
        tokens = lexer.tokenize()
    """

    def __init__(self, source: str, filename: str = '<stdin>'):
        # Normalize line endings to \n
        self.source: str = source.replace('\r\n', '\n').replace('\r', '\n')
        self.filename: str = filename

        # Position tracking (Unicode code point indices, not bytes)
        self.pos: int = 0           # Current index into self.source
        self.line: int = 1          # Current line (1-indexed)
        self.column: int = 1        # Current column (1-indexed)

        # Output
        self.tokens: List[Token] = []

        # Indentation state
        self.indent_stack: List[int] = [0]
        self.at_line_start: bool = True

        # Bracket nesting depth for implicit line continuation
        self.paren_depth: int = 0

        # FFI raw-capture state
        self._ffi_pending: bool = False   # True after seeing ٻاهري
        self._ffi_armed: bool = False     # True after ٻاهري + ڪم sequence
        self._ffi_base_indent: int = 0    # Indent level before FFI body

    # ─────────────────────────────────────────────────────────────
    # Source Navigation
    # ─────────────────────────────────────────────────────────────

    def _cur(self) -> str:
        """Current character, or '' at EOF."""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return ''

    def _peek(self, offset: int = 1) -> str:
        """Look ahead by offset characters."""
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return ''

    def _advance(self) -> str:
        """Consume and return the current character, updating line/col."""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _at_end(self) -> bool:
        """True if all source has been consumed."""
        return self.pos >= len(self.source)

    # ─────────────────────────────────────────────────────────────
    # Error Helpers
    # ─────────────────────────────────────────────────────────────

    def _error(self, message: str, line: int = None, col: int = None) -> LexerError:
        """Create a LexerError at the given or current position."""
        return LexerError(
            message,
            line or self.line,
            col or self.column,
            self.filename
        )

    # ─────────────────────────────────────────────────────────────
    # Token Emission
    # ─────────────────────────────────────────────────────────────

    def _emit(self, ttype: TokenType, value: str,
              line: int, col: int, original: Optional[str] = None):
        """Append a token to the output list."""
        self.tokens.append(Token(ttype, value, line, col, original))

    # ─────────────────────────────────────────────────────────────
    # Main Tokenization Loop
    # ─────────────────────────────────────────────────────────────

    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire source and return the token list.

        Main entry point. Handles:
          1. Line-start indentation → INDENT / DEDENT
          2. Whitespace / tabs (error) / newlines
          3. Comments (# to end of line)
          4. Line continuation (backslash)
          5. F-strings (f"..." / f'...')
          6. Strings ("..." / '...')
          7. Numbers (Arabic & Sindhi digits, decimal points)
          8. Single-char operators (۽, ۾)
          9. Word tokens → keyword / operator / identifier
          10. Symbols ( ) [ ] { } : = . ،
          11. FFI raw-capture when armed
        """
        # Reset state
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1
        self.indent_stack = [0]
        self.at_line_start = True
        self.paren_depth = 0
        self._ffi_pending = False
        self._ffi_armed = False
        self._ffi_base_indent = 0

        while not self._at_end():
            # ── FFI raw-capture mode ──
            if self._ffi_armed and self.at_line_start:
                # Check if we're entering the FFI body
                if self._try_enter_ffi():
                    continue

            ch = self._cur()

            # ── Line start → indentation ──
            if self.at_line_start:
                self._handle_indentation()
                continue

            # ── Inline whitespace ──
            if ch == ' ':
                self._advance()
                continue

            # ── Tab → error ──
            if ch == '\t':
                raise self._error(
                    "\u0679\u064A\u0628 \u0627\u06AA\u0634\u0631 "
                    "\u0627\u0633\u062A\u0639\u0645\u0627\u0644 "
                    "\u06AA\u0631\u06BB\u0646 \u0645\u0646\u0639 "
                    "\u0622\u0647\u064A\u06D4 \u0645\u0647\u0631"
                    "\u0628\u0627\u0646\u064A \u06AA\u0631\u064A "
                    "\u06F4 \u062E\u0627\u0644\u064A "
                    "\u062C\u0627\u0621\u0650 \u0627\u0633\u062A"
                    "\u0639\u0645\u0627\u0644 \u06AA\u0631\u064A\u0648"
                )  # "ٽيب اکر استعمال ڪرڻ منع آهي. مهرباني ڪري ۴ خالي جاءِ استعمال ڪريو"

            # ── Newline ──
            if ch == '\n':
                self._handle_newline()
                continue

            # ── Comment ──
            if ch == '#':
                self._skip_comment()
                continue

            # ── Line continuation (backslash + newline) ──
            if ch == '\\' and self._peek() == '\n':
                self._advance()  # skip \
                self._advance()  # skip \n
                continue

            # ── F-string (f"..." or f'...') ──
            if ch == 'f' and self._peek() in ('"', "'"):
                self._read_fstring()
                continue

            # ── String literal ──
            if ch in ('"', "'"):
                self._read_string()
                continue

            # ── Number literal ──
            if is_any_digit(ch):
                self._read_number()
                continue

            # ── Single-char operators (۽, ۾) ──
            if ch in SINGLE_CHAR_OPERATORS:
                line, col = self.line, self.column
                self._advance()
                self._emit(TokenType.OPERATOR, ch, line, col)
                continue

            # ── Word: identifier / keyword / word-operator ──
            if is_identifier_start(ch):
                self._read_word()
                continue

            # ── Symbol ──
            if ch in SYMBOLS:
                self._read_symbol()
                continue

            # ── Unknown character ──
            cp = ord(ch)
            raise self._error(
                f"\u0627\u06BB \u0633\u06C3\u0627\u062A\u0644 "
                f"\u0627\u06AA\u0634\u0631: '{ch}' (U+{cp:04X})"
            )  # "اڻ سڃاتل اکر"

        # ── End of file: emit trailing NEWLINE + DEDENTs + EOF ──
        self._finalize()
        return self.tokens

    # ─────────────────────────────────────────────────────────────
    # Indentation (INDENT / DEDENT)
    # ─────────────────────────────────────────────────────────────

    def _handle_indentation(self):
        """
        Process indentation at the start of a logical line.

        Rules:
          • 4 spaces = 1 indentation level
          • Tabs are a lexer error
          • Blank lines and comment-only lines are skipped
          • Indent increase → INDENT token(s)
          • Indent decrease → DEDENT token(s)
          • Mismatched indent → error
        """
        start_line = self.line
        indent = 0

        # Count leading spaces
        while not self._at_end() and self._cur() == ' ':
            self._advance()
            indent += 1

        # Tab check
        if not self._at_end() and self._cur() == '\t':
            raise self._error(
                "\u0679\u064A\u0628 \u0627\u06AA\u0634\u0631 "
                "\u0627\u0633\u062A\u0639\u0645\u0627\u0644 "
                "\u06AA\u0631\u06BB\u0646 \u0645\u0646\u0639 "
                "\u0622\u0647\u064A\u06D4 \u0645\u0647\u0631"
                "\u0628\u0627\u0646\u064A \u06AA\u0631\u064A "
                "\u06F4 \u062E\u0627\u0644\u064A "
                "\u062C\u0627\u0621\u0650 \u0627\u0633\u062A"
                "\u0639\u0645\u0627\u0644 \u06AA\u0631\u064A\u0648"
            )

        # Skip blank lines (empty or whitespace-only)
        if self._at_end() or self._cur() == '\n':
            if not self._at_end():
                self._advance()  # consume \n
            self.at_line_start = True
            return

        # Skip comment-only lines
        if self._cur() == '#':
            self._skip_comment()
            self.at_line_start = True
            return

        # ── Process indentation change ──
        self.at_line_start = False
        current = self.indent_stack[-1]

        if indent > current:
            # Verify it's a multiple of 4 increase
            if (indent - current) % 4 != 0:
                raise self._error(
                    f"\u063A\u0644\u0637 \u0627\u0646\u062F\u0631\u0627\u062C: "
                    f"{indent} \u062E\u0627\u0644\u064A "
                    f"\u062C\u0627\u0621\u0650 \u0645\u0644\u064A\u0627\u060C "
                    f"\u067E\u0631 {current + 4} "
                    f"\u0645\u062A\u0648\u0642\u0639 \u0647\u064A\u0627",
                    start_line, 1
                )

            # Emit INDENT for each 4-space level increase
            levels = (indent - current) // 4
            for _ in range(levels):
                self.indent_stack.append(self.indent_stack[-1] + 4)
                self._emit(TokenType.INDENT, '', start_line, 1)

        elif indent < current:
            # Pop indent stack, emitting DEDENT for each level
            while self.indent_stack[-1] > indent:
                self.indent_stack.pop()
                self._emit(TokenType.DEDENT, '', start_line, 1)

            if self.indent_stack[-1] != indent:
                raise self._error(
                    f"\u063A\u0644\u0637 \u0627\u0646\u062F\u0631\u0627\u062C: "
                    f"{indent} \u062E\u0627\u0644\u064A "
                    f"\u062C\u0627\u0621\u0650 \u06AA\u0646\u0647\u0646 "
                    f"\u0628\u0647 \u0627\u06B3\u064A\u0646 "
                    f"\u0633\u0637\u062D \u0633\u0627\u0646 "
                    f"\u0646\u0647 \u0645\u0644\u0646",
                    start_line, 1
                )

        # else: indent == current, no tokens emitted

    def _handle_newline(self):
        """Emit NEWLINE token (suppressed inside brackets)."""
        line, col = self.line, self.column
        self._advance()  # consume \n

        if self.paren_depth == 0:
            self._emit(TokenType.NEWLINE, '\\n', line, col)

        self.at_line_start = True

    def _finalize(self):
        """Emit final NEWLINE, DEDENTs, and EOF."""
        # Emit trailing NEWLINE if needed
        if (self.tokens and
                self.tokens[-1].type not in (
                    TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT)):
            self._emit(TokenType.NEWLINE, '\\n', self.line, self.column)

        # Emit DEDENTs for any remaining indentation
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self._emit(TokenType.DEDENT, '', self.line, self.column)

        self._emit(TokenType.EOF, '', self.line, self.column)

    # ─────────────────────────────────────────────────────────────
    # Comments
    # ─────────────────────────────────────────────────────────────

    def _skip_comment(self):
        """Skip from # to end of line. Comments are not emitted."""
        while not self._at_end() and self._cur() != '\n':
            self._advance()
        # The newline itself will be handled on the next iteration

    # ─────────────────────────────────────────────────────────────
    # String Literals
    # ─────────────────────────────────────────────────────────────

    def _read_string(self):
        """
        Read a string literal delimited by " or '.
        Supports escape sequences: \\n \\t \\\\ \\" \\'
        """
        line, col = self.line, self.column
        quote = self._advance()  # consume opening quote
        value = ''

        while not self._at_end():
            ch = self._cur()

            if ch == '\n':
                raise self._error(
                    "\u0645\u062A\u0646 \u06BE "
                    "\u0646\u0626\u064A\u0646 \u0633\u0679 "
                    "\u0645\u0644\u064A\u0648 \u2014 "
                    "\u0645\u062A\u0646 \u0628\u0646\u062F "
                    "\u06AA\u0631\u064A\u0648",
                    line, col
                )  # "متن ۾ نئين سٽ مليو — متن بند ڪريو"

            if ch == '\\':
                self._advance()  # skip backslash
                if self._at_end():
                    raise self._error(
                        "\u0645\u062A\u0646 \u06BE "
                        "\u0641\u0631\u0627\u0631 \u062A\u0633\u0644\u0633\u0644 "
                        "\u0627\u06BB\u0645\u06AA\u0645\u0644 "
                        "\u0622\u0647\u064A",
                        line, col
                    )  # "متن ۾ فرار تسلسل اڻمڪمل آهي"
                esc = self._advance()
                if esc in ESCAPE_MAP:
                    value += ESCAPE_MAP[esc]
                else:
                    raise self._error(
                        f"\u0627\u06BB\u0633\u06C3\u0627\u062A\u0644 "
                        f"\u0641\u0631\u0627\u0631 \u062A\u0633\u0644"
                        f"\u0633\u0644: '\\{esc}'",
                        line, col
                    )  # "اڻسڃاتل فرار تسلسل"
                continue

            if ch == quote:
                self._advance()  # consume closing quote
                self._emit(TokenType.STRING, value, line, col)
                return

            value += self._advance()

        raise self._error(
            f"\u0645\u062A\u0646 \u0628\u0646\u062F \u0646\u0647 "
            f"\u062B\u064A\u0648 \u2014 \u0628\u0646\u062F "
            f"\u06AA\u0631\u06BB\u0646 \u0648\u0627\u0631\u0648 "
            f"{quote} \u0646\u0634\u0627\u0646 \u0646\u0647 "
            f"\u0645\u0644\u064A\u0648",
            line, col
        )  # "متن بند نه ٿيو — بند ڪرڻ وارو X نشان نه مليو"

    # ─────────────────────────────────────────────────────────────
    # F-String Literals
    # ─────────────────────────────────────────────────────────────

    def _read_fstring(self):
        """
        Read an f-string (f"..." or f'...').

        Embedded expressions in {braces} are stored as-is in the
        token value. Expression parsing is deferred to the parser.
        """
        line, col = self.line, self.column
        self._advance()  # skip 'f'
        quote = self._advance()  # opening quote
        value = ''
        brace_depth = 0

        while not self._at_end():
            ch = self._cur()

            if ch == '\n':
                raise self._error(
                    "f-\u0645\u062A\u0646 \u06BE "
                    "\u0646\u0626\u064A\u0646 \u0633\u0679 "
                    "\u0645\u0644\u064A\u0648 \u2014 "
                    "\u0645\u062A\u0646 \u0628\u0646\u062F "
                    "\u06AA\u0631\u064A\u0648",
                    line, col
                )

            if ch == '\\':
                self._advance()
                if self._at_end():
                    raise self._error(
                        "f-\u0645\u062A\u0646 \u06BE "
                        "\u0641\u0631\u0627\u0631 \u062A\u0633\u0644"
                        "\u0633\u0644 \u0627\u06BB\u0645\u06AA\u0645\u0644 "
                        "\u0622\u0647\u064A",
                        line, col
                    )
                esc = self._advance()
                if esc in ESCAPE_MAP:
                    value += ESCAPE_MAP[esc]
                else:
                    raise self._error(
                        f"\u0627\u06BB\u0633\u06C3\u0627\u062A\u0644 "
                        f"\u0641\u0631\u0627\u0631 \u062A\u0633\u0644"
                        f"\u0633\u0644: '\\{esc}'",
                        line, col
                    )
                continue

            if ch == '{':
                brace_depth += 1
                value += self._advance()
                continue

            if ch == '}':
                if brace_depth > 0:
                    brace_depth -= 1
                value += self._advance()
                continue

            if ch == quote and brace_depth == 0:
                self._advance()  # closing quote
                self._emit(TokenType.FSTRING, value, line, col)
                return

            value += self._advance()

        raise self._error(
            f"f-\u0645\u062A\u0646 \u0628\u0646\u062F \u0646\u0647 "
            f"\u062B\u064A\u0648 \u2014 \u0628\u0646\u062F "
            f"\u06AA\u0631\u06BB\u0646 \u0648\u0627\u0631\u0648 "
            f"{quote} \u0646\u0634\u0627\u0646 \u0646\u0647 "
            f"\u0645\u0644\u064A\u0648",
            line, col
        )

    # ─────────────────────────────────────────────────────────────
    # Number Literals
    # ─────────────────────────────────────────────────────────────

    def _read_number(self):
        """
        Read an integer or float literal.

        Accepts both Arabic (0-9) and Sindhi (۰-۹) digits.
        Stores the Arabic form as value and preserves the original
        Sindhi form for error messages.
        """
        line, col = self.line, self.column
        original = ''
        has_dot = False

        while not self._at_end():
            ch = self._cur()

            if ch == '.':
                if has_dot:
                    break  # second dot → stop (it's attribute access)
                # Only treat as decimal if followed by a digit
                if not is_any_digit(self._peek()):
                    break
                has_dot = True
                original += self._advance()
                continue

            if is_any_digit(ch):
                original += self._advance()
                continue

            break  # non-digit, non-dot → end of number

        arabic = sindhi_to_arabic(original)
        self._emit(
            TokenType.NUMBER, arabic, line, col,
            original if original != arabic else None
        )

    # ─────────────────────────────────────────────────────────────
    # Word Tokens (Identifiers, Keywords, Word Operators)
    # ─────────────────────────────────────────────────────────────

    def _read_word(self):
        """
        Read a word token: identifier, keyword, or word operator.

        Maximal-munch: reads the full word (letters + digits + _),
        then classifies it as keyword, operator, or identifier.
        """
        line, col = self.line, self.column
        word = ''

        while not self._at_end() and is_identifier_char(self._cur()):
            word += self._advance()

        # ── Keyword? ──
        if word in KEYWORDS:
            self._emit(TokenType.KEYWORD, word, line, col)

            # FFI state tracking
            if word == 'ٻاهري':  # ٻاهري
                self._ffi_pending = True
            elif word == 'ڪم':  # ڪم
                if self._ffi_pending:
                    self._ffi_armed = True
                    self._ffi_pending = False
                # (if not pending, just a normal ڪم keyword)
            else:
                # Any other keyword resets FFI pending state
                self._ffi_pending = False
            return

        # ── Word operator? ──
        if word in WORD_OPERATORS:
            self._emit(TokenType.OPERATOR, word, line, col)
            self._ffi_pending = False  # operators reset FFI pending
            return

        # ── Identifier — enforce naming rules ──
        self._ffi_pending = False
        self._enforce_naming_rules(word, line, col)
        self._emit(TokenType.IDENTIFIER, word, line, col)

    def _enforce_naming_rules(self, identifier: str, line: int, col: int):
        """
        Enforce Phase 0 naming rules on user-defined identifiers.

        Rule: No _-separated component of an identifier may be
        identical to a keyword or operator name. This prevents
        identifiers like "my_نه_value" (contains نه operator) or
        "my_غلطي_handler" (contains غلطي keyword).

        Note: This checks _-separated COMPONENTS, not arbitrary
        substrings. A word like "بيان" (naturally containing "يا")
        is fine because the lexer reads full words atomically.
        """
        if '_' not in identifier:
            return  # Single-word identifiers — no component check needed

        parts = identifier.split('_')
        for part in parts:
            if not part:
                continue  # skip empty parts from leading/trailing _

            if part in KEYWORDS:
                raise self._error(
                    f"\u0633\u06C3\u0627\u06BB\u067E \u0646\u0627\u0644\u0648 "
                    f"'{identifier}' \u06BE "
                    f"\u0645\u062D\u0641\u0648\u0638 \u0644\u0641\u0638 "
                    f"'{part}' \u0634\u0627\u0645\u0644 "
                    f"\u0622\u0647\u064A\u060C "
                    f"\u062C\u064A\u06AA\u0648 \u0645\u0646\u0639 "
                    f"\u0622\u0647\u064A",
                    line, col
                )  # "سڃاڻپ نالو 'X' ۾ محفوظ لفظ 'Y' شامل آهي، جيڪو منع آهي"

            if part in WORD_OPERATORS:
                raise self._error(
                    f"\u0633\u06C3\u0627\u06BB\u067E \u0646\u0627\u0644\u0648 "
                    f"'{identifier}' \u06BE "
                    f"\u0622\u067E\u0631\u064A\u0679\u0631 "
                    f"'{part}' \u0634\u0627\u0645\u0644 "
                    f"\u0622\u0647\u064A\u060C "
                    f"\u062C\u064A\u06AA\u0648 \u0645\u0646\u0639 "
                    f"\u0622\u0647\u064A",
                    line, col
                )  # "سڃاڻپ نالو 'X' ۾ آپريٽر 'Y' شامل آهي، جيڪو منع آهي"

    # ─────────────────────────────────────────────────────────────
    # Symbol Tokens
    # ─────────────────────────────────────────────────────────────

    def _read_symbol(self):
        """Read a symbol/punctuation character and track bracket depth."""
        line, col = self.line, self.column
        ch = self._advance()

        # Track bracket nesting for implicit line continuation
        if ch in '([{':
            self.paren_depth += 1
        elif ch in ')]}':
            if self.paren_depth <= 0:
                # Error names brackets explicitly (spec bidi rule)
                bracket_name = {')': ')', ']': ']', '}': '}'}.get(ch, ch)
                raise self._error(
                    f"\u0627\u0636\u0627\u0641\u064A \u0628\u0646\u062F "
                    f"\u06AA\u0631\u06BB\u0646 \u0648\u0627\u0631\u0648 "
                    f"\u0646\u0634\u0627\u0646 '{bracket_name}' \u0645\u0644\u064A\u0648 "
                    f"\u0628\u063A\u064A\u0631 \u0645\u0644\u0646\u062F\u0691 "
                    f"\u06A9\u06BE\u0648\u0644\u06BB\u0646 \u0648\u0627\u0631\u0648 "
                    f"\u0646\u0634\u0627\u0646",
                    line, col
                )  # "اضافي بند ڪرڻ وارو نشان ')' مليو بغير ملندڙ کولڻ وارو نشان"
            self.paren_depth -= 1

        self._emit(TokenType.SYMBOL, ch, line, col)

    # ─────────────────────────────────────────────────────────────
    # FFI Raw-Capture Mode
    # ─────────────────────────────────────────────────────────────
    #
    # When the lexer encounters the ٻاهري keyword immediately
    # preceding a ڪم function header, it tokenizes the header
    # normally (name, params, colon). Upon hitting the NEWLINE+INDENT
    # that opens the function body, it SWITCHES TO RAW_PYTHON CAPTURE
    # MODE: it stops Sindhi tokenization and instead reads raw text
    # lines verbatim (still tracking indentation depth using plain
    # whitespace counting, not Sindhi token rules) until it reaches
    # a DEDENT back to the original level.
    #
    # That raw text is packaged as a single RAW_PYTHON token
    # attached to the function's AST node — the parser does not
    # attempt to parse it as Sindhi statements at all.
    # ─────────────────────────────────────────────────────────────

    def _try_enter_ffi(self) -> bool:
        """
        Check if the current line starts an FFI body, and if so,
        capture it. Returns True if FFI capture was performed.

        Called when _ffi_armed is True and we're at a line start.
        """
        # Save position to potentially rewind
        saved_pos = self.pos
        saved_line = self.line
        saved_col = self.column

        # Count indentation
        indent = 0
        while not self._at_end() and self._cur() == ' ':
            self._advance()
            indent += 1

        current_indent = self.indent_stack[-1]

        if indent > current_indent:
            # This is the FFI body — enter capture mode
            body_indent = indent
            self._ffi_base_indent = current_indent

            # Push indent and emit INDENT
            self.indent_stack.append(indent)
            self._emit(TokenType.INDENT, '', saved_line, 1)

            # Capture the body
            self._capture_ffi_body(body_indent, saved_line)
            return True
        else:
            # Not an indented body — rewind and let normal processing handle it
            self.pos = saved_pos
            self.line = saved_line
            self.column = saved_col
            self._ffi_armed = False
            return False

    def _capture_ffi_body(self, body_indent: int, start_line: int):
        """
        Read the raw Python body of an ٻاهري function.

        Reads lines verbatim until indentation returns to or below
        the function header's level. Preserves relative indentation
        within the body.
        """
        raw_lines = []

        # ── First line (indentation already consumed) ──
        first_line = ''
        while not self._at_end() and self._cur() != '\n':
            first_line += self._advance()
        if not self._at_end():
            self._advance()  # consume \n
        raw_lines.append(first_line)

        # ── Subsequent lines ──
        while not self._at_end():
            saved_pos = self.pos
            saved_line = self.line
            saved_col = self.column

            # Count leading spaces
            indent = 0
            while not self._at_end() and self._cur() == ' ':
                self._advance()
                indent += 1

            # Blank line
            if self._at_end() or self._cur() == '\n':
                if not self._at_end():
                    self._advance()  # consume \n
                raw_lines.append('')
                continue

            # Dedented back to or below base level → end of body
            if indent <= self._ffi_base_indent:
                self.pos = saved_pos
                self.line = saved_line
                self.column = saved_col
                break

            # Read rest of line with relative indentation preserved
            relative = max(0, indent - body_indent)
            line_text = ' ' * relative
            while not self._at_end() and self._cur() != '\n':
                line_text += self._advance()
            if not self._at_end():
                self._advance()  # consume \n
            raw_lines.append(line_text)

        # ── Emit RAW_PYTHON token ──
        raw_body = '\n'.join(raw_lines).rstrip('\n')
        self._emit(TokenType.RAW_PYTHON, raw_body, start_line, 1)

        # ── Clean up: DEDENT and reset FFI state ──
        self.indent_stack.pop()
        self._emit(TokenType.DEDENT, '', self.line, 1)
        self._ffi_armed = False
        self.at_line_start = True


# ═════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════

def tokenize(source: str, filename: str = '<stdin>') -> List[Token]:
    """
    Convenience function: tokenize source code and return the token list.

    Args:
        source:   Source code string (UTF-8 Python str)
        filename: Source filename for error messages

    Returns:
        List of Token objects, ending with an EOF token.

    Raises:
        LexerError: On invalid syntax (tabs, unterminated strings,
                    bad indentation, naming rule violations, etc.)
    """
    return Lexer(source, filename).tokenize()


def tokenize_file(filepath: str) -> List[Token]:
    """
    Read a file with encoding='utf-8' and tokenize it.

    Args:
        filepath: Path to the .سن source file

    Returns:
        List of Token objects

    Raises:
        LexerError: On invalid syntax
        FileNotFoundError: If file doesn't exist
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return Lexer(source, filepath).tokenize()
