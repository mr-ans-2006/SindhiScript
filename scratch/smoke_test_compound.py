import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from سنڌي.lexer import tokenize
from سنڌي.parser import Parser
from سنڌي.evaluator import Evaluator

source_valid = """
# Test ZWNJ (U+200C) inside identifiers
متغير سنڌي‌ٻولي = "سنڌي ٻولي"
متغير جيڪڏهن‌نه = 42
متغير دلخوش = "خوش"

ڇاپ("مرڪب لفظ 1: "، سنڌي‌ٻولي)
ڇاپ("مرڪب لفظ 2: "، جيڪڏهن‌نه)
"""

source_invalid = """
# Test ZWNJ (U+200C) at the start of an identifier (should fail)
متغير ‌سنڌي = "غلط"
"""

try:
    print("--- Tokenizing Valid Source ---")
    tokens = tokenize(source_valid, "test_compound.سن")
    print("--- Parsing Valid Source ---")
    parser = Parser(tokens, "test_compound.سن")
    ast = parser.parse()
    print("--- Evaluating Valid Source ---")
    evaluator = Evaluator()
    evaluator.interpret(ast)
    print("\n✅ Valid compound words parsed and evaluated successfully!")
except Exception as e:
    print(f"❌ Valid compound words test failed unexpectedly: {e}")
    sys.exit(1)

try:
    print("\n--- Tokenizing Invalid Source (Leading ZWNJ) ---")
    tokens = tokenize(source_invalid, "test_compound_invalid.سن")
    print(f"❌ Error: Lexer incorrectly accepted leading ZWNJ! Tokens: {tokens}")
    sys.exit(1)
except Exception as e:
    print(f"✅ Expected error caught for leading ZWNJ: {e}")
