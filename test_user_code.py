import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from سنڌي.lexer import tokenize
from سنڌي.parser import Parser
from سنڌي.evaluator import Evaluator
import builtins

code = """
ڪم ڳڻپ_مشين(الف، ب، عمل):
    جيڪڏهن عمل برابر "+":
        موٽايو الف جمع ب
    ٻي_صورت عمل برابر "-":
        موٽايو الف گهٽائڻ ب
    ٻي_صورت عمل برابر "*":
        موٽايو الف ضرب ب
    ٻي_صورت عمل برابر "/":
        جيڪڏهن ب برابر 0:
            موٽايو "غلطي: ٻُڙي سان تقسيم نه ٿي سگهي!"
        موٽايو الف تقسيم ب
    نه_ته:
        موٽايو "غلط عمل"

ڇاپ("--- سادي ڳڻپ مشين ---")
متغير پهريون = اعشاري(داخل_ڪرو("پهريون عدد ڏيو: "))
متغير ٻيو = اعشاري(داخل_ڪرو("ٻيو عدد ڏيو: "))
متغير عمل = داخل_ڪرو("عمل ڏيو (+, -, *, /): ")

متغير نتيجو = ڳڻپ_مشين(پهريون، ٻيو، عمل)
ڇاپ("نتيجو آهي:"، نتيجو)
"""

inputs = ['45', '78', '+']
builtins.input = lambda p: inputs.pop(0) if inputs else ""

tokens = tokenize(code, 'test')
parser = Parser(tokens, 'test')
ast = parser.parse()
eval = Evaluator()
try:
    eval.interpret(ast)
except Exception as e:
    print("ERROR CAUGHT:", e)

# ---------------------------------------------------------------------------
# Demo security tests (added 2026-10-30). These test the BROWSER DEMO's
# limits, not the plain interpreter above, so they run through
# docs/demo_run.py against docs/interpreter (the demo's patched
# interpreter). The plain interpreter above has no step budget or interop
# allowlist by design — that is why this section swaps the Sindhi modules
# out first: this file already imported the plain interpreter for the
# calculator demo, and Python would otherwise reuse those modules.
# Run: python test_user_code.py — ten assertions, all fast, no network.
# ---------------------------------------------------------------------------
_DEMO_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), "docs")
_DEMO_INTERP = os.path.join(_DEMO_ROOT, "interpreter")
for _m in [m for m in list(sys.modules) if m == "سنڌي" or m.startswith("سنڌي.")]:
    del sys.modules[_m]
sys.path.insert(0, _DEMO_INTERP)
sys.path.insert(0, _DEMO_ROOT)
import demo_run


def _demo(code, modules=None):
    return demo_run.run_demo(code, None, modules)


# 1-2. Infinite loop -> Sindhi step error (status + message).
_r = _demo("جڏهن_تائين صحيح:\n    ڇاپ(\"loop\")\n")
assert _r["status"] == "step-limit", _r
assert "قدم جي حد پوري ٿي وئي" in (_r["error"] or ""), _r
# 3. Deep recursion -> frame error.
_r = _demo("ڪم ڳڻ(عدد):\n    جيڪڏهن عدد برابر 0:\n        موٽايو 0\n    موٽايو ڳڻ(عدد گهٽائڻ 1)\nڇاپ(ڳڻ(10000))\n")
assert _r["status"] == "recursion-limit", _r
# 4. 10M list -> memory error.
_r = _demo("متغير فهرست = حد(0, 10000000)\nڇاپ(فهرست)\n")
assert _r["status"] == "memory-limit", _r
# 5-6. XSS outputs come back as literal text (page renders with textContent).
_r = _demo('ڇاپ("<img src=x onerror=alert(1)>")\n')
assert _r["status"] == "ok" and "<img src=x onerror=alert(1)>" in _r["output"], _r
_r = _demo('ڇاپ("<script>alert(1)</script>")\n')
assert _r["status"] == "ok" and "<script>alert(1)</script>" in _r["output"], _r
# 7-9. Blocked extern imports refused.
for _mod in ["os", "js", "pyodide.http"]:
    _r = _demo(f"ٻاهري ڪم خراب():\n    import {_mod}\n    return 1\n\nڇاپ(خراب())\n")
    assert _r["status"] == "interop-blocked", (_mod, _r)
# 10. Module path traversal refused (lexer rejects the path before it runs).
_r = _demo("آندو ../../x\n")
assert _r["status"] == "error", _r

print("Demo security tests: 10/10 passed")
