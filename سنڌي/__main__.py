# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — CLI Entry Point

Usage:
  python -m سنڌي [flags] [script.سن]

Flags:
  --مدد          Show help message
  --نسخو         Show version
  --فونٽ_جانچ    Run terminal font diagnostic
  --رومن         Enable Roman fallback transliteration for output
"""
import sys
import os

from . import __version__
from . import terminal
from .errors import install_sindhi_excepthook, SindhiError
from .repl import start_repl
from .lexer import tokenize
from .parser import Parser
from .evaluator import Evaluator


def print_help():
    terminal.print_output("\n--- سنڌي (SindhiScript) ---")
    terminal.print_output(f"نسخو (Version): {__version__}")
    terminal.print_output("\nاستعمال (Usage):")
    terminal.print_output("  python -m سنڌي [جھنڊا] [فائل.سن]")
    terminal.print_output("\nجھنڊا (Flags):")
    terminal.print_output("  --مدد          هي مدد ڏيکاريو")
    terminal.print_output("  --نسخو         نسخو ڏيکاريو")
    terminal.print_output("  --فونٽ_جانچ    ٽرمينل ۾ فونٽ جي جانچ ڪريو")
    terminal.print_output("  --رومن         آئوٽ پٽ کي رومن (Latin) ۾ تبديل ڪريو")
    terminal.print_output("\nجيڪڏهن ڪو به فائل نه ڏنو ويو، ته REPL (انٽرايڪٽو موڊ) شروع ٿيندو.")
    terminal.print_output("----------------------------\n")


def run_file(filepath: str):
    if not os.path.exists(filepath):
        print(f"غلطي: فائل '{filepath}' نه مليو.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
    except UnicodeDecodeError:
        print(f"غلطي: فائل '{filepath}' UTF-8 ۾ انڪوڊ ٿيل نه آهي.", file=sys.stderr)
        print("مهرباني ڪري فائل کي UTF-8 انڪوڊنگ ۾ محفوظ ڪريو.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"غلطي: فائل ਪڙهڻ ۾ مسئلو: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        tokens = tokenize(source, filepath)
        parser = Parser(tokens, filepath)
        ast = parser.parse()
        evaluator = Evaluator()
        evaluator.interpret(ast)
    except SindhiError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    terminal.setup_terminal()
    install_sindhi_excepthook()
    
    args = sys.argv[1:]
    
    # Check flags
    script_file = None
    for arg in args:
        if arg == '--مدد':
            print_help()
            sys.exit(0)
        elif arg == '--نسخو':
            terminal.print_output(f"سنڌي (SindhiScript) {__version__}")
            sys.exit(0)
        elif arg == '--فونٽ_جانچ':
            terminal.run_font_check()
            sys.exit(0)
        elif arg == '--رومن':
            terminal.ROMAN_MODE_ENABLED = True
        elif not arg.startswith('--'):
            script_file = arg
            
    if script_file:
        run_file(script_file)
    else:
        start_repl()


if __name__ == "__main__":
    main()
