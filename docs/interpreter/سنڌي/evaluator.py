# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Tree-Walking Evaluator
"""
import random
import math
import time
from typing import Any, List, Callable

from .ast_nodes import *
from .environment import Environment
from .errors import RuntimeError

# ─── DEMO PATCH (browser demo only — not in the original repo) ────────────
# Resource limits + sandboxing for the public Pyodide demo. See SECURITY.md.
import ast as _demo_ast
import builtins as _demo_builtins_module
import datetime as _demo_datetime
import json as _demo_json

DEMO_STEP_BUDGET = 300000
DEMO_MAX_CALL_DEPTH = 400
DEMO_MAX_COLLECTION = 1000000
DEMO_MAX_POWER_BITS = 4000000


def _demo_err(message, kind, node=None):
    """RuntimeError carrying a machine-readable demo_kind for the harness."""
    err = RuntimeError(message, node)
    err.demo_kind = kind
    return err


_DEMO_EXTERN_ALLOWED_MODULES = ("math", "random", "json", "datetime")
_DEMO_EXTERN_BANNED_NAMES = {
    "eval", "exec", "compile", "open", "__import__", "globals", "locals",
    "vars", "getattr", "setattr", "delattr", "breakpoint", "help", "input",
    "memoryview", "exit", "quit",
}


def _demo_extern_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Allowlist-only __import__ for extern code (backstop to AST checks)."""
    root = name.split(".")[0] if name else ""
    if level != 0 or root not in _DEMO_EXTERN_ALLOWED_MODULES:
        raise ImportError(
            f"Demo ۾ ماڊيول '{name}' جي اجازت نه آهي (module import blocked in demo)")
    return _demo_builtins_module.__import__(name, globals, locals, fromlist, level)


_DEMO_EXTERN_SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "chr": chr,
    "dict": dict, "divmod": divmod, "enumerate": enumerate, "filter": filter,
    "float": float, "format": format, "frozenset": frozenset, "hash": hash,
    "hex": hex, "int": int, "isinstance": isinstance, "iter": iter,
    "len": len, "list": list, "map": map, "max": max, "min": min,
    "next": next, "oct": oct, "ord": ord, "pow": pow, "print": print,
    "range": range, "repr": repr, "reversed": reversed, "round": round,
    "set": set, "slice": slice, "sorted": sorted, "str": str, "sum": sum,
    "tuple": tuple, "zip": zip,
    "ArithmeticError": ArithmeticError, "AssertionError": AssertionError,
    "AttributeError": AttributeError, "Exception": Exception,
    "IndexError": IndexError, "KeyError": KeyError, "LookupError": LookupError,
    "NameError": NameError, "OverflowError": OverflowError,
    "RuntimeError": RuntimeError, "StopIteration": StopIteration,
    "TypeError": TypeError, "ValueError": ValueError,
    "ZeroDivisionError": ZeroDivisionError,
    "__import__": _demo_extern_import,
}


def _demo_validate_extern_code(wrapper_source, node):
    """AST checks on extern (Python-interop) code before it ever runs.

    Rejects: imports outside the allowlist, relative imports, private
    (dunder) attribute access, and dangerous builtin names. String contents
    are never inspected, so Sindhi text cannot false-positive.
    """
    try:
        tree = _demo_ast.parse(wrapper_source)
    except SyntaxError as e:
        raise _demo_err(
            f"ٻاهري پائيٿون ڪوڊ ۾ نحوي غلطي: {e} (syntax error in extern code)",
            "interop-blocked", node)
    func_def = tree.body[0]
    for sub in _demo_ast.walk(func_def):
        if isinstance(sub, _demo_ast.Import):
            for alias in sub.names:
                root = alias.name.split(".")[0]
                if root not in _DEMO_EXTERN_ALLOWED_MODULES:
                    raise _demo_err(
                        f"ٻاهري ڪوڊ ۾ ماڊيول '{root}' جي اجازت نه آهي "
                        "(module import blocked in demo)",
                        "interop-blocked", node)
        elif isinstance(sub, _demo_ast.ImportFrom):
            if sub.level != 0:
                raise _demo_err(
                    "ٻاهري ڪوڊ ۾ لاڳاپيل امپورٽ جي اجازت نه آهي "
                    "(relative imports blocked in demo)",
                    "interop-blocked", node)
            root = sub.module.split(".")[0] if sub.module else ""
            if root not in _DEMO_EXTERN_ALLOWED_MODULES:
                raise _demo_err(
                    f"ٻاهري ڪوڊ ۾ ماڊيول '{root}' جي اجازت نه آهي "
                    "(module import blocked in demo)",
                    "interop-blocked", node)
        elif isinstance(sub, _demo_ast.Attribute):
            if sub.attr.startswith("_"):
                raise _demo_err(
                    f"ٻاهري ڪوڊ ۾ خانگي خاصيت '{sub.attr}' جي اجازت نه آهي "
                    "(private attribute access blocked in demo)",
                    "interop-blocked", node)
        elif isinstance(sub, _demo_ast.Name):
            if sub.id in _DEMO_EXTERN_BANNED_NAMES or sub.id.startswith("__"):
                raise _demo_err(
                    f"ٻاهري ڪوڊ ۾ نالو '{sub.id}' جي اجازت نه آهي "
                    "(name blocked in demo)",
                    "interop-blocked", node)



# ─── Value → text (used by ڇاپ، متن and f-strings) ─────────────────────────

def sindhi_repr(val: Any) -> str:
    """Like repr(), but booleans are written as صحيح / غلط."""
    if val is True:
        return 'صحيح'
    if val is False:
        return 'غلط'
    if isinstance(val, list):
        return '[' + ', '.join(sindhi_repr(v) for v in val) + ']'
    if isinstance(val, tuple):
        inner = ', '.join(sindhi_repr(v) for v in val)
        return '(' + inner + (',)' if len(val) == 1 else ')')
    if isinstance(val, dict):
        return '{' + ', '.join(f'{sindhi_repr(k)}: {sindhi_repr(v)}' for k, v in val.items()) + '}'
    if isinstance(val, str):
        return repr(val)
    return str(val)


def sindhi_str(val: Any) -> str:
    """Like str(), but booleans are written as صحيح / غلط."""
    if isinstance(val, str):
        return val
    return sindhi_repr(val)


def split_fstring(text: str) -> List[tuple]:
    """
    Split the body of an f-string into parts:
      ('text', 'literal text')  and  ('expr', 'expression source', 'format spec')
    {{ and }} are literal braces, like Python.
    """
    parts = []
    buf = ''
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '{' and i + 1 < n and text[i + 1] == '{':
            buf += '{'
            i += 2
            continue
        if ch == '}' and i + 1 < n and text[i + 1] == '}':
            buf += '}'
            i += 2
            continue
        if ch == '{':
            if buf:
                parts.append(('text', buf))
                buf = ''
            # find the matching }, skipping nested brackets and strings
            depth = 0
            quote = None
            spec_at = -1
            j = i + 1
            while j < n:
                c = text[j]
                if quote:
                    if c == '\\':
                        j += 2
                        continue
                    if c == quote:
                        quote = None
                elif c in '"\'':
                    quote = c
                elif c in '([{':
                    depth += 1
                elif c in ')]':
                    depth -= 1
                elif c == '}':
                    if depth == 0:
                        break
                    depth -= 1
                elif c == ':' and depth == 0 and spec_at < 0:
                    spec_at = j
                j += 1
            if j >= n:
                raise ValueError("'{' بند نه ٿيو")
            if spec_at >= 0:
                parts.append(('expr', text[i + 1:spec_at], text[spec_at + 1:j]))
            else:
                parts.append(('expr', text[i + 1:j], ''))
            i = j + 1
            continue
        if ch == '}':
            raise ValueError("اڪيلو '}' مليو — '}}' استعمال ڪريو")
        buf += ch
        i += 1
    if buf:
        parts.append(('text', buf))
    return parts


class ReturnException(Exception):
    def __init__(self, value: Any):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


# ─── Callable Types ─────────────────────────────────────────────────────────

class SindhiCallable:
    def arity(self) -> int:
        raise NotImplementedError
        
    def call(self, evaluator, arguments: List[Any], node=None) -> Any:
        raise NotImplementedError
        
    def __str__(self):
        return "<callable>"


class SindhiFunction(SindhiCallable):
    def __init__(self, declaration: FunctionDecl, closure: Environment):
        self.declaration = declaration
        self.closure = closure

    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, evaluator, arguments: List[Any], node=None) -> Any:
        # DEMO PATCH: Sindhi-level recursion cap (500 frames).
        depth = getattr(evaluator, "_demo_call_depth", 0) + 1
        evaluator._demo_call_depth = depth
        if depth > DEMO_MAX_CALL_DEPTH:
            evaluator._demo_call_depth = depth - 1
            raise _demo_err(
                "فليٽ (recursion) جي حد پوري ٿي وئي (recursion limit exceeded)",
                "recursion-limit", node)
        try:
            env = Environment(self.closure)
            for i, param in enumerate(self.declaration.params):
                env.define(param, arguments[i])

            if self.declaration.is_extern:
                return self._call_extern(evaluator, env, arguments)

            try:
                evaluator.execute_block(self.declaration.body.statements, env)
            except ReturnException as ret:
                return ret.value

            return None
        finally:
            evaluator._demo_call_depth = getattr(evaluator, "_demo_call_depth", 1) - 1
    def _call_extern(self, evaluator, env: Environment, arguments: List[Any]) -> Any:
        # DEMO PATCH: extern code runs under AST validation + restricted
        # builtins + an import allowlist (math, random, json, datetime only).
        # The original exposed full builtins via exec(); that is the leak.
        extern_node = self.declaration.body.statements[0]
        code = extern_node.code

        # We wrap the python code into a function to properly bind variables and return values
        param_list = ", ".join(self.declaration.params)

        # Indent the user code by 4 spaces
        indented_code = "\n".join("    " + line for line in code.split("\n"))

        wrapper = f"def __sindhi_extern_wrapper({param_list}):\n{indented_code}\n"
        _demo_validate_extern_code(wrapper, extern_node)

        local_scope = {}
        global_scope = {
            "__builtins__": _DEMO_EXTERN_SAFE_BUILTINS,
            "math": math,
            "random": random,
            "json": _demo_json,
            "datetime": _demo_datetime,
        }

        try:
            exec(wrapper, global_scope, local_scope)
            func = local_scope['__sindhi_extern_wrapper']
            return func(*arguments)
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"ٻاهري پائيٿون ڪوڊ ۾ غلطي: {e}", extern_node)
    def bind(self, instance):
        env = Environment(self.closure)
        env.define('پنهنجو', instance)
        return SindhiFunction(self.declaration, env)

    def __str__(self):
        return f"<ڪم {self.declaration.name}>"


class SindhiClass(SindhiCallable):
    def __init__(self, name: str, superclass: Optional['SindhiClass'], methods: dict):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def find_method(self, name: str):
        if name in self.methods:
            return self.methods[name]
        if self.superclass is not None:
            return self.superclass.find_method(name)
        return None

    def arity(self) -> int:
        initializer = self.find_method("پيدائش")
        if initializer is not None:
            return initializer.arity()
        return 0

    def call(self, evaluator, arguments, node=None) -> Any:
        instance = SindhiInstance(self)
        initializer = self.find_method("پيدائش")
        if initializer is not None:
            initializer.bind(instance).call(evaluator, arguments, node)
        return instance

    def __str__(self):
        return f"<طبقو {self.name}>"


class SindhiInstance:
    def __init__(self, klass: SindhiClass):
        self.klass = klass
        self.fields = {}

    def get(self, name: str, node=None):
        if name in self.fields:
            return self.fields[name]
            
        method = self.klass.find_method(name)
        if method is not None:
            return method.bind(self)
            
        raise RuntimeError(f"ملڪيت '{name}' اڻ سڃاتل آهي", node)

    def set(self, name: str, value: Any):
        self.fields[name] = value

    def __str__(self):
        return f"<{self.klass.name} جو حصو>"


# ─── Evaluator ──────────────────────────────────────────────────────────────

class Evaluator:
    def __init__(self, filename: str = '<stdin>'):
        from .module_loader import ModuleLoader
        self.filename = filename
        self.globals = Environment()
        self.environment = self.globals
        self.module_loader = ModuleLoader(self)
        # DEMO PATCH: per-evaluator resource counters.
        self._demo_steps = 0
        self._demo_call_depth = 0
        self._define_builtins()

    def _define_builtins(self):
        from .stdlib import setup_builtins
        setup_builtins(self.globals)

    def interpret(self, program: Program):
        # Runtime errors are passed up to the caller (CLI, REPL, web IDE),
        # so a failing script exits non-zero and shows its real file name.
        try:
            for stmt in program.statements:
                self.execute(stmt)
        except RuntimeError as e:
            if e.filename == '<stdin>':
                e.set_filename(self.filename)
            raise

    def execute(self, stmt: Statement):
        # DEMO PATCH: step budget (graceful error before the 5s hard kill).
        self._demo_steps = getattr(self, "_demo_steps", 0) + 1
        if self._demo_steps > DEMO_STEP_BUDGET:
            raise _demo_err(
                "قدم جي حد پوري ٿي وئي — پروگرام تمام ڊگهو هليو (step limit exceeded)",
                "step-limit", stmt)
        method_name = f'visit_{stmt.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(stmt)

    def evaluate(self, expr: Expression) -> Any:
        # DEMO PATCH: step budget (graceful error before the 5s hard kill).
        self._demo_steps = getattr(self, "_demo_steps", 0) + 1
        if self._demo_steps > DEMO_STEP_BUDGET:
            raise _demo_err(
                "قدم جي حد پوري ٿي وئي — پروگرام تمام ڊگهو هليو (step limit exceeded)",
                "step-limit", expr)
        method_name = f'visit_{expr.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(expr)

    def generic_visit(self, node):
        raise Exception(f"No visit_{node.__class__.__name__} method")

    def execute_block(self, statements: List[Statement], environment: Environment):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    # ─── Statement Visitors ───

    def visit_ExpressionStatement(self, stmt: ExpressionStatement):
        self.evaluate(stmt.expression)

    def visit_VarDecl(self, stmt: VarDecl):
        value = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)
        # define(name, value, is_const)
        self.environment.define(stmt.name, value, stmt.is_const)

    def visit_Block(self, stmt: Block):
        self.execute_block(stmt.statements, Environment(self.environment))

    def visit_IfStmt(self, stmt: IfStmt):
        if self._is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.then_branch)
            return

        for cond, block in stmt.elif_branches:
            if self._is_truthy(self.evaluate(cond)):
                self.execute(block)
                return

        if stmt.else_branch is not None:
            self.execute(stmt.else_branch)

    def visit_WhileStmt(self, stmt: WhileStmt):
        while self._is_truthy(self.evaluate(stmt.condition)):
            try:
                self.execute(stmt.body)
            except BreakException:
                break
            except ContinueException:
                continue

    def visit_ForStmt(self, stmt: ForStmt):
        iterable = self.evaluate(stmt.iterable)
        
        # Enforce it is iterable in Python sense
        try:
            iterator = iter(iterable)
        except TypeError:
            raise RuntimeError(f"هن کي ڦيرائي (iterate) نٿو سگهجي: {iterable}", stmt)

        for item in iterator:
            env = Environment(self.environment)
            env.define(stmt.item_name, item)
            
            try:
                self.execute_block(stmt.body.statements, env)
            except BreakException:
                break
            except ContinueException:
                continue

    def visit_FunctionDecl(self, stmt: FunctionDecl):
        function = SindhiFunction(stmt, self.environment)
        self.environment.define(stmt.name, function)

    def visit_ClassDecl(self, stmt: ClassDecl):
        superclass = None
        if stmt.superclass is not None:
            superclass = self.environment.get(stmt.superclass, stmt)
            if not isinstance(superclass, SindhiClass):
                raise RuntimeError(f"ورثي لاءِ ڪلاس ضروري آهي، پر '{stmt.superclass}' مليل آهي", stmt)

        env = self.environment
        if superclass is not None:
            env = Environment(self.environment)
            env.define("نئون", superclass)

        methods = {}
        for method_decl in stmt.methods:
            func = SindhiFunction(method_decl, env)
            methods[method_decl.name] = func

        klass = SindhiClass(stmt.name, superclass, methods)
        
        self.environment.define(stmt.name, klass)

    def visit_ReturnStmt(self, stmt: ReturnStmt):
        value = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)
        raise ReturnException(value)

    def visit_ImportStmt(self, stmt: ImportStmt):
        mod_env = self.module_loader.load_module(stmt.module_name, stmt)
        self.environment.define(stmt.module_name, mod_env)

    def visit_FromImportStmt(self, stmt: FromImportStmt):
        mod_env = self.module_loader.load_module(stmt.module_name, stmt)
        for name in stmt.names:
            # We fetch from the module environment
            try:
                val = mod_env.get(name, stmt)
                self.environment.define(name, val)
            except RuntimeError as e:
                raise RuntimeError(f"نالو '{name}' ماڊيول '{stmt.module_name}' ۾ نه مليو", stmt)

    def visit_ExportStmt(self, stmt: ExportStmt):
        exports = []
        try:
            exports = self.environment.get('__exports__')
        except RuntimeError:
            self.environment.define('__exports__', [])
            exports = self.environment.get('__exports__')
            
        for name in stmt.names:
            exports.append(name)

    def visit_BreakStmt(self, stmt: BreakStmt):
        raise BreakException()

    def visit_ContinueStmt(self, stmt: ContinueStmt):
        raise ContinueException()

    def visit_TryStmt(self, stmt: TryStmt):
        try:
            self.execute(stmt.try_block)
        except RuntimeError as e:
            if stmt.catch_block:
                env = Environment(self.environment)
                if stmt.catch_name:
                    env.define(stmt.catch_name, str(e))
                self.execute_block(stmt.catch_block.statements, env)
            elif not stmt.finally_block:
                raise e # re-raise if no catch and no finally (should be parsed out)
        finally:
            if stmt.finally_block:
                self.execute(stmt.finally_block)

    # ─── Expression Visitors ───

    def visit_NumberLiteral(self, expr: NumberLiteral):
        return expr.value

    def visit_StringLiteral(self, expr: StringLiteral):
        if not expr.is_fstring:
            return expr.value
            
        # f-string: each {expression} is lexed, parsed and evaluated in the
        # current scope. {قدر:.2f} style format specs are passed to format().
        parts = getattr(expr, '_fstring_parts', None)
        if parts is None:
            from .lexer import tokenize
            from .parser import Parser
            try:
                raw_parts = split_fstring(expr.value)
            except ValueError as e:
                raise RuntimeError(f"f-متن ۾ غلطي: {e}", expr)
            parts = []
            for part in raw_parts:
                if part[0] == 'text':
                    parts.append(part)
                    continue
                source = part[1].strip()
                if not source:
                    raise RuntimeError("f-متن ۾ خالي {} مليو", expr)
                program = Parser(tokenize(source + '\n', self.filename), self.filename).parse()
                if len(program.statements) != 1 or not isinstance(program.statements[0], ExpressionStatement):
                    raise RuntimeError(f"f-متن ۾ رڳو اظهار (expression) لکي سگهجي ٿو: {source}", expr)
                parts.append(('expr', program.statements[0].expression, part[2]))
            expr._fstring_parts = parts

        out = []
        for part in parts:
            if part[0] == 'text':
                out.append(part[1])
                continue
            value = self.evaluate(part[1])
            if part[2]:
                try:
                    out.append(format(value, part[2]))
                except (ValueError, TypeError) as e:
                    raise RuntimeError(f"f-متن جي فارميٽ '{part[2]}' ۾ غلطي: {e}", expr)
            else:
                out.append(sindhi_str(value))
        return ''.join(out)

    def visit_BooleanLiteral(self, expr: BooleanLiteral):
        return expr.value

    def visit_NullLiteral(self, expr: NullLiteral):
        return None

    def visit_Identifier(self, expr: Identifier):
        return self.environment.get(expr.value, expr)

    def visit_ListLiteral(self, expr: ListLiteral):
        # DEMO PATCH: collection size ceiling.
        if len(expr.elements) > DEMO_MAX_COLLECTION:
            raise _demo_err("فهرست تمام وڏي آهي (list too large for demo)", "memory-limit", expr)
        return [self.evaluate(el) for el in expr.elements]

    def visit_DictLiteral(self, expr: DictLiteral):
        # DEMO PATCH: collection size ceiling.
        if len(expr.keys) > DEMO_MAX_COLLECTION:
            raise _demo_err("لغت تمام وڏي آهي (dict too large for demo)", "memory-limit", expr)
        result = {}
        for k, v in zip(expr.keys, expr.values):
            key = self.evaluate(k)
            val = self.evaluate(v)
            result[key] = val
        return result

    def visit_Assignment(self, expr: Assignment):
        value = self.evaluate(expr.value)
        if isinstance(expr.target, Identifier):
            self.environment.assign(expr.target.value, value, expr)
        elif isinstance(expr.target, MemberAccess):
            obj = self.evaluate(expr.target.obj)
            if not isinstance(obj, SindhiInstance):
                raise RuntimeError("رڳو طبقي جي حصي (instance) ۾ ملڪيت رکي سگهجي ٿي", expr)
            obj.set(expr.target.property, value)
        elif isinstance(expr.target, IndexAccess):
            obj = self.evaluate(expr.target.obj)
            idx = self.evaluate(expr.target.index)
            try:
                obj[idx] = value
            except Exception as e:
                raise RuntimeError(f"انڊيڪس اسائنمينٽ ۾ غلطي: {e}", expr)
        else:
            raise RuntimeError("غير قانوني اسائنمينٽ ٽارگيٽ", expr)
        return value

    def visit_BinaryOp(self, expr: BinaryOp):
        left = self.evaluate(expr.left)
        
        # Short-circuit logical operators
        if expr.op == 'يا':
            if self._is_truthy(left):
                return left
            return self.evaluate(expr.right)
        
        if expr.op == '۽':
            if not self._is_truthy(left):
                return left
            return self.evaluate(expr.right)
            
        right = self.evaluate(expr.right)
        # DEMO PATCH: guard against single-step memory blowups.
        if expr.op == 'ضرب':
            for _seq, _num in ((left, right), (right, left)):
                if isinstance(_seq, (str, list)) and isinstance(_num, int) and _num > 0:
                    if len(_seq) * _num > DEMO_MAX_COLLECTION:
                        raise _demo_err("نتيجو تمام وڏو آهي (result too large for demo)", "memory-limit", expr)
        if expr.op == 'طاقت':
            if isinstance(left, int) and isinstance(right, int) and right > 0 and abs(left) > 1:
                if right * max(1, abs(left).bit_length()) > DEMO_MAX_POWER_BITS:
                    raise _demo_err("طاقت جو نتيجو تمام وڏو آهي (power result too large for demo)", "memory-limit", expr)
        
        try:
            if expr.op == 'جمع':
                return left + right
            elif expr.op == 'گهٽائڻ':
                return left - right
            elif expr.op == 'ضرب':
                return left * right
            elif expr.op == 'تقسيم':
                return left / right
            elif expr.op == 'باقي':
                return left % right
            elif expr.op == 'طاقت':
                return left ** right
            elif expr.op == 'وڌيڪ':
                return left > right
            elif expr.op == 'گهٽ':
                return left < right
            elif expr.op == 'وڌيڪ_برابر':
                return left >= right
            elif expr.op == 'گهٽ_برابر':
                return left <= right
            elif expr.op == 'برابر':
                return left == right
            elif expr.op == 'نه_برابر':
                return left != right
            elif expr.op == '۾':
                return left in right
        except TypeError as e:
            raise RuntimeError(f"نشان '{expr.op}' لاءِ غلط ڊيٽا قِسم", expr)
        except Exception as e:
            raise RuntimeError(f"حسابي غلطي: {e}", expr)

    def visit_UnaryOp(self, expr: UnaryOp):
        right = self.evaluate(expr.right)
        
        if expr.op == 'نه':
            return not self._is_truthy(right)
        elif expr.op == 'گهٽائڻ':
            if not isinstance(right, (int, float)):
                raise RuntimeError("گهٽائڻ لاءِ عدد هجڻ گهرجي", expr)
            return -right
        elif expr.op == 'جمع':
            if not isinstance(right, (int, float)):
                raise RuntimeError("جمع لاءِ عدد هجڻ گهرجي", expr)
            return +right

    def visit_Call(self, expr: Call):
        callee = self.evaluate(expr.callee)
        
        arguments = []
        for arg in expr.arguments:
            arguments.append(self.evaluate(arg))
            
        if not isinstance(callee, SindhiCallable):
            raise RuntimeError("هن کي سڏي نٿو سگهجي", expr)
            
        if callee.arity() != -1 and len(arguments) != callee.arity():
            raise RuntimeError(f"توقع ڪيل {callee.arity()} آرگيومينٽس، پر مليا {len(arguments)}", expr)
            
        return callee.call(self, arguments, expr)
        
    def visit_IndexAccess(self, expr: IndexAccess):
        obj = self.evaluate(expr.obj)
        index = self.evaluate(expr.index)
        try:
            return obj[index]
        except KeyError:
            raise RuntimeError(f"لغت ۾ ڪنجي '{index}' نه ملي", expr)
        except IndexError:
            raise RuntimeError(f"فهرست جو انڊيڪس '{index}' حد کان ٻاهر آهي", expr)
        except Exception as e:
            raise RuntimeError(f"انڊيڪس استعمال ڪرڻ ۾ غلطي: {e}", expr)
            
    def visit_MemberAccess(self, expr: MemberAccess):
        obj = self.evaluate(expr.obj)
        
        if isinstance(obj, SindhiInstance):
            return obj.get(expr.property, expr)
        if isinstance(obj, Environment):
            return obj.get(expr.property, expr)
            
        # We can add primitive property access later if desired, e.g. for str/list.
        raise RuntimeError("ملڪيت جو استعمال رڳو طبقن يا ماڊيول تي ٿي سگهي ٿو", expr)

    def _is_truthy(self, val: Any) -> bool:
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        return bool(val)
