# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Module Loader
"""
import os
from .lexer import tokenize
from .parser import Parser
from .environment import Environment
from .errors import RuntimeError
from .stdlib import setup_builtins

class ModuleLoader:
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.cache = {}

    def load_module(self, module_name: str, node=None) -> Environment:
        """Loads a module and returns its Environment (exported variables)."""
        if module_name in self.cache:
            return self.cache[module_name]

        # Prevent circular imports immediately
        self.cache[module_name] = Environment()

        filepath = f"{module_name}.سن"
        if not os.path.exists(filepath):
            raise RuntimeError(f"ماڊيول '{module_name}' ({filepath}) نه مليو", node)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
        except UnicodeDecodeError:
            raise RuntimeError(f"ماڊيول '{filepath}' UTF-8 ۾ انڪوڊ ٿيل نه آهي", node)
        except Exception as e:
            raise RuntimeError(f"ماڊيول پڙهڻ ۾ مسئلو: {e}", node)

        tokens = tokenize(source, filepath)
        parser = Parser(tokens, filepath)
        ast = parser.parse()

        # Execute in a fresh environment
        mod_env = Environment()
        setup_builtins(mod_env)
        
        # We also want the module to know about the module_loader if it imports things
        # This requires Evaluator to use THIS ModuleLoader. We achieve this by letting
        # the evaluator execute the block with the new environment.
        self.evaluator.execute_block(ast.statements, mod_env)

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
