# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Module Loader — DEMO VERSION.

This replaces the original module_loader.py for the browser demo ONLY.
The original reads .سن files from the working directory (os.path.exists /
os.listdir / open) — that is a path-traversal surface (T6) and has no
meaning in a browser. This version never touches the filesystem: modules
load ONLY from the in-memory DEMO_MODULES dict supplied by the demo
harness, keyed by module name. Any name that is not in the dict — including
paths with /, \\, .. or absolute paths — is refused with a clear error.
"""
from .lexer import tokenize
from .parser import Parser
from .environment import Environment
from .errors import RuntimeError
from .stdlib import setup_builtins

# name -> source text. Set by demo_run.run_demo() on every run.
# Only the bundled examples are ever put here.
DEMO_MODULES = {}


def _demo_module_err(message, node):
    err = RuntimeError(message, node)
    err.demo_kind = "module-blocked"
    return err


class ModuleLoader:
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.cache = {}

    def load_module(self, module_name: str, node=None) -> Environment:
        """Loads a module and returns its Environment (exported variables)."""
        if module_name in self.cache:
            return self.cache[module_name]

        # Path validation (defense in depth — no filesystem is touched at
        # all, but a hostile name must never even reach the lookup).
        if (not isinstance(module_name, str)
                or not module_name
                or module_name.startswith("/")
                or "\\" in module_name
                or "/" in module_name
                or ".." in module_name
                or module_name.startswith(".")
                or "\x00" in module_name):
            raise _demo_module_err(
                f"ماڊيول '{module_name}' جي اجازت نه آهي "
                "(module path rejected in demo)", node)

        if module_name not in DEMO_MODULES:
            raise _demo_module_err(
                f"ماڊيول '{module_name}' ڊيمو ۾ موجود نه آهي "
                "(module not available in demo)", node)

        # Prevent circular imports immediately
        self.cache[module_name] = Environment()

        filepath = f"demo:{module_name}.سن"
        source = DEMO_MODULES[module_name]

        tokens = tokenize(source, filepath)
        parser = Parser(tokens, filepath)
        ast = parser.parse()

        # Execute in a fresh environment
        mod_env = Environment()
        setup_builtins(mod_env)

        try:
            self.evaluator.execute_block(ast.statements, mod_env)
        except RuntimeError as e:
            if e.filename == '<stdin>':
                e.set_filename(filepath)
            raise

        # After execution, what does it export?
        # If 'جاريات' (exports) is defined in the module's environment (as a special variable),
        # we only return those. Otherwise, we return all definitions for now to keep it simple.
        exports = mod_env.get('__exports__', None) if '__exports__' in mod_env.values else None

        export_env = Environment()
        if exports:
            for name in exports:
                if name in mod_env.values:
                    export_env.define(name, mod_env.values[name])
                else:
                    raise RuntimeError(f"جاريات ۾ ڏنل نالو '{name}' ماڊيول ۾ نه مليو", node)
        else:
            # Export everything not built-in (heuristic)
            for k, v in mod_env.values.items():
                if not (isinstance(v, type) or callable(v) or k == '__exports__'): # very rough
                    export_env.define(k, v)
            export_env = mod_env # just return everything

        self.cache[module_name] = export_env
        return export_env
