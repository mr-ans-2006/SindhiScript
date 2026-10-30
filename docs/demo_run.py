# -*- coding: utf-8 -*-
"""SindhiScript browser-demo harness (demo-only file, not part of the repo).

Runs SindhiScript source with the demo's resource limits and returns plain
text. Pure Python — no Pyodide imports — so the same code is tested with
system Python and runs unchanged inside the Pyodide worker.

Run pipeline mirrors web_ide.py: tokenize -> Parser -> Evaluator.interpret,
with stdout captured and Sindhi errors surfaced as text. Differences from
web_ide.py (all deliberate, see SECURITY.md):
  * input() is fed from pre-supplied lines only (workers cannot wait on
    the UI); a clean error is raised when the lines run out.
  * modules come from an in-memory dict of bundled examples only.
  * output is capped at 1,000,000 characters (defense in depth, T2).
"""
import builtins
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTERP = os.path.join(_HERE, "interpreter")
if _INTERP not in sys.path:
    sys.path.insert(0, _INTERP)

from سنڌي.lexer import tokenize
from سنڌي.parser import Parser
from سنڌي.evaluator import Evaluator
from سنڌي.errors import SindhiError, RuntimeError as SindhiRuntimeError
from سنڌي import module_loader

MAX_OUTPUT_CHARS = 1000000

_KIND_TO_STATUS = {
    "step-limit": "step-limit",
    "memory-limit": "memory-limit",
    "recursion-limit": "recursion-limit",
    "module-blocked": "module-blocked",
    "interop-blocked": "interop-blocked",
    "blocked": "blocked",
    "input-exhausted": "input-exhausted",
}


def run_demo(source, stdin_lines=None, modules=None):
    """Run one program. Returns {status, output, error} — all plain text."""
    module_loader.DEMO_MODULES = dict(modules or {})
    lines = [str(x) for x in (stdin_lines or [])]
    state = {"index": 0}
    out_buf = io.StringIO()
    old_stdout = sys.stdout
    old_input = builtins.input
    old_limit = sys.getrecursionlimit()

    def feeder(prompt=""):
        # Matches web_ide.py: print the prompt, echo the line, return it.
        if prompt:
            print(prompt, end="", flush=True)
        if state["index"] >= len(lines):
            err = SindhiRuntimeError(
                "داخل ڪرڻ لاءِ وڌيڪ سٽون نه آهن "
                "(no more input lines — add lines to the input box)", None)
            err.demo_kind = "input-exhausted"
            raise err
        line = lines[state["index"]]
        state["index"] += 1
        print(line)
        return line

    sys.stdout = out_buf
    builtins.input = feeder
    try:
        # Python-level backstop for recursion the Sindhi cap cannot see
        # (e.g. deeply nested parentheses in the parser). 3000 is chosen
        # from measurement: 500 Sindhi call levels use ~3000 Python frames
        # and run cleanly in Pyodide, while 10000 nested parens overflow
        # the wasm stack before a 20000 limit can trip. The Sindhi cap
        # (400 levels, ~2400 frames) therefore always trips first for
        # function recursion, and this limit catches parser recursion —
        # both as a clean RecursionError, never a wasm crash.
        sys.setrecursionlimit(3000)
    except Exception:
        pass
    status = "ok"
    error = None
    try:
        tokens = tokenize(source, "demo.سن")
        program = Parser(tokens, "demo.سن").parse()
        Evaluator("demo.سن").interpret(program)
    except SindhiError as e:
        status = _KIND_TO_STATUS.get(getattr(e, "demo_kind", None), "error")
        error = str(e)
    except RecursionError:
        status = "recursion-limit"
        error = ("غلطي [demo.سن]: رن_ٽائم_غلطي\n"
                 "فليٽ (recursion) جي حد پوري ٿي وئي (recursion limit exceeded)")
    except MemoryError:
        status = "memory-limit"
        error = ("غلطي [demo.سن]: رن_ٽائم_غلطي\n"
                 "ميموري ختم ٿي وئي (memory limit exceeded)")
    except SystemExit:
        status = "exited"
    except Exception as e:  # never leak a traceback to the page
        status = "error"
        error = f"غلطي: {e}"
    finally:
        sys.stdout = old_stdout
        builtins.input = old_input
        try:
            sys.setrecursionlimit(old_limit)
        except Exception:
            pass
    output = out_buf.getvalue()
    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + "\n[output truncated — demo limit]"
    return {"status": status, "output": output, "error": error}


def run_demo_json(payload_json):
    """JSON in / JSON out wrapper for the worker (avoids proxy pitfalls)."""
    payload = json.loads(payload_json)
    result = run_demo(
        payload.get("source", ""),
        payload.get("stdin", []),
        payload.get("modules", {}),
    )
    return json.dumps(result, ensure_ascii=False)
