# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Interactive REPL
"""
import sys

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

from . import terminal
from .errors import install_sindhi_excepthook, SindhiError
from .lexer import tokenize
from .parser import Parser
from .evaluator import Evaluator


def print_help():
    terminal.print_output("\n--- سنڌي REPL مدد ---")
    terminal.print_output(".نڪرو        - REPL مان نڪرڻ لاءِ (يا Ctrl+C دٻايو)")
    terminal.print_output(".فونٽ_جانچ   - ٽرمينل ۾ فونٽ جي جانچ ڪرڻ لاءِ")
    terminal.print_output(".رومن        - رومن (Latin) اسڪرپٽ ۾ آئوٽ پٽ ڏسڻ لاءِ (ٽوگل)")
    terminal.print_output(".ترجمو       - AST ترجمو (ڊيبگ) ڏيکارڻ لاءِ (ٽوگل)")
    terminal.print_output(".مدد         - هي مدد ڏيکارڻ لاءِ")
    terminal.print_output("----------------------\n")


def start_repl():
    # Setup terminal environment and warning checks
    terminal.setup_terminal()
    
    # Install global exception hook for uncaught python errors
    install_sindhi_excepthook()
    
    terminal.print_output("سنڌي (SindhiScript) REPL ۾ ڀليڪار!")
    terminal.print_output("مدد لاءِ '.مدد' لکو، نڪرڻ لاءِ '.نڪرو' لکو.")
    
    evaluator = Evaluator()
    show_ast = False
    
    while True:
        try:
            # We use a custom prompt for Sindhi
            prompt = "سنڌي> "
            if terminal.ROMAN_MODE_ENABLED:
                prompt = "sindhi> "
                
            if HAS_PROMPT_TOOLKIT:
                # Keybindings for multi-line support
                kb = KeyBindings()
                # Esc + Enter (or Alt+Enter) to submit
                @kb.add('escape', 'enter')
                def _(event):
                    event.current_buffer.validate_and_handle()
                
                # Try to bind Ctrl+Enter if terminal supports it (some do, some don't)
                try:
                    @kb.add('c-enter')
                    def _(event):
                        event.current_buffer.validate_and_handle()
                except Exception:
                    pass

                session = PromptSession(key_bindings=kb, multiline=True)
                # Print a helpful hint for the first time
                if getattr(start_repl, 'first_run', True):
                    terminal.print_output("[اشارو: نئين لائن لاءِ Enter، ڪوڊ هلائڻ لاءِ Alt+Enter دٻايو]")
                    start_repl.first_run = False
                    
                line = session.prompt(prompt)
            else:
                line = input(prompt)
            
            # Handle empty input
            if not line.strip():
                continue
                
            # Handle dot commands
            cmd = line.strip()
            if cmd == ".نڪرو":
                break
            elif cmd == ".مدد":
                print_help()
                continue
            elif cmd == ".فونٽ_جانچ":
                terminal.run_font_check()
                continue
            elif cmd == ".رومن":
                terminal.ROMAN_MODE_ENABLED = not terminal.ROMAN_MODE_ENABLED
                status = "فعال" if terminal.ROMAN_MODE_ENABLED else "غير فعال"
                terminal.print_output(f"رومن موڊ {status} ڪيو ويو.")
                continue
            elif cmd == ".ترجمو":
                show_ast = not show_ast
                status = "فعال" if show_ast else "غير فعال"
                terminal.print_output(f"AST ترجمو موڊ {status} ڪيو ويو.")
                continue

            # Multiline accumulation
            source = line + "\n"
            
            # Simple heuristic for multiline: if it ends with ':' or has unbalanced brackets,
            # or is currently indented, we keep reading until an empty line.
            if line.strip().endswith(':') or line.startswith(' ') or line.startswith('\t'):
                while True:
                    cont_prompt = " ...> " if not terminal.ROMAN_MODE_ENABLED else " ...> "
                    cont_line = input(cont_prompt)
                    if not cont_line.strip():
                        # Empty line signals end of multiline block
                        source += "\n"
                        break
                    source += cont_line + "\n"
            
            # Execute
            try:
                tokens = tokenize(source, "<repl>")
                parser = Parser(tokens, "<repl>")
                ast = parser.parse()
                
                if show_ast:
                    print("--- AST ---")
                    print(ast)
                    print("-----------")
                    
                evaluator.interpret(ast)
            except SindhiError as e:
                # SindhiErrors are already formatted, just print to stderr
                print(e, file=sys.stderr)
            except Exception as e:
                # Any other unexpected errors
                import traceback
                traceback.print_exc()

        except KeyboardInterrupt:
            print("\nپروگرام بند ڪيو ويو (KeyboardInterrupt)")
            break
        except EOFError:
            print()
            break
