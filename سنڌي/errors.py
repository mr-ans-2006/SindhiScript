# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Error Handling & Formatter
"""
import sys
import traceback
from typing import Optional


class SindhiError(Exception):
    """Base class for all formatted SindhiScript exceptions."""
    def __init__(self, message: str, error_type: str, line: int, col: int, filename: str):
        self.sindhi_message = message
        self.error_type = error_type
        self.line = line
        self.col = col
        self.filename = filename
        super().__init__(self._format())

    def _format(self) -> str:
        # Format:
        # غلطي [فائل_نالو:سٽ:ڪالم]: غلطي_جو_قسم
        # <تفصيل>
        # فائل: <فائل_نالو>، سٽ <سٽ_نمبر>، ڪالم <ڪالم_نمبر>
        return (
            f"\u063A\u0644\u0637\u064A [{self.filename}:"
            f"{self.line}:{self.col}]: "
            f"{self.error_type}\n"
            f"{self.sindhi_message}\n"
            f"\u0641\u0627\u0626\u0644: {self.filename}\u060C "
            f"\u0633\u0679 {self.line}\u060C "
            f"\u06AA\u0627\u0644\u0645 {self.col}"
        )


class LexerError(SindhiError):
    def __init__(self, message: str, line: int, column: int, filename: str = '<stdin>'):
        super().__init__(message, "نحوي_غلطي", line, column, filename)


class ParseError(SindhiError):
    def __init__(self, message: str, token, filename: str = '<stdin>'):
        self.token = token
        super().__init__(message, "نحوي_غلطي", token.line, token.column, filename)


class RuntimeError(SindhiError):
    def __init__(self, message: str, node=None, filename: str = '<stdin>'):
        self.node = node
        line = getattr(node, 'line', '?') if node else '?'
        col = getattr(node, 'col', '?') if node else '?'
        super().__init__(message, "رن_ٽاﺋﻢ_غلطي", line, col, filename)


def install_sindhi_excepthook():
    """
    Installs a global exception hook that intercepts native Python
    exceptions (like recursion depth, memory errors, zero division)
    and formats them as Sindhi error messages.
    """
    def sindhi_excepthook(exc_type, exc_value, exc_traceback):
        # If it's already a formatted Sindhi error, just print it
        if isinstance(exc_value, SindhiError):
            print(str(exc_value), file=sys.stderr)
            return

        # Handle keyboard interrupt gracefully
        if issubclass(exc_type, KeyboardInterrupt):
            print("\nپروگرام بند ڪيو ويو (KeyboardInterrupt)", file=sys.stderr)
            return

        # For pure Python errors, extract the last frame if possible
        filename = "<native>"
        line = "?"
        col = "?"
        
        if exc_traceback:
            # Get the deepest frame
            tb = traceback.extract_tb(exc_traceback)
            if tb:
                last_frame = tb[-1]
                filename = last_frame.filename
                line = last_frame.lineno
        
        # Translate common Python error types to Sindhi
        sindhi_msg = str(exc_value)
        if issubclass(exc_type, RecursionError):
            sindhi_msg = "فليٽ (recursion) جي حد پوري ٿي وئي"
        elif issubclass(exc_type, ZeroDivisionError):
            sindhi_msg = "ٻڙي سان تقسيم ڪرڻ منع آهي"
        elif issubclass(exc_type, MemoryError):
            sindhi_msg = "ميموري ختم ٿي وئي"
        elif issubclass(exc_type, TypeError):
            sindhi_msg = f"غلط ڊيٽا قِسم: {exc_value}"

        error_msg = (
            f"\u063A\u0644\u0637\u064A [{filename}:{line}:{col}]: سسٽم_غلطي\n"
            f"{sindhi_msg}\n"
            f"\u0641\u0627\u0626\u0644: {filename}\u060C \u0633\u0679 {line}\u060C \u06AA\u0627\u0644\u0645 {col}"
        )
        print(error_msg, file=sys.stderr)

    sys.excepthook = sindhi_excepthook
