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

    def _call_extern(self, evaluator, env: Environment, arguments: List[Any]) -> Any:
        # Extern function contains a single ExternBlockNode
        extern_node = self.declaration.body.statements[0]
        code = extern_node.code
        
        # We wrap the python code into a function to properly bind variables and return values
        param_list = ", ".join(self.declaration.params)
        
        # Indent the user code by 4 spaces
        indented_code = "\n".join("    " + line for line in code.split("\n"))
        
        wrapper = f"def __sindhi_extern_wrapper({param_list}):\n{indented_code}\n"
        
        local_scope = {}
        global_scope = {
            'math': math,
            'time': time,
            'random': random,
        }
        
        try:
            exec(wrapper, global_scope, local_scope)
            func = local_scope['__sindhi_extern_wrapper']
            return func(*arguments)
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
    def __init__(self):
        from .module_loader import ModuleLoader
        self.globals = Environment()
        self.environment = self.globals
        self.module_loader = ModuleLoader(self)
        self._define_builtins()

    def _define_builtins(self):
        from .stdlib import setup_builtins
        setup_builtins(self.globals)

    def interpret(self, program: Program):
        try:
            for stmt in program.statements:
                self.execute(stmt)
        except RuntimeError as e:
            import sys
            print(e, file=sys.stderr)

    def execute(self, stmt: Statement):
        method_name = f'visit_{stmt.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(stmt)

    def evaluate(self, expr: Expression) -> Any:
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
            
        # Basic f-string implementation for phase 4:
        # In a full language we would parse expressions inside {}.
        # For this prototype we will just return the literal (or use regex to eval locals).
        return expr.value

    def visit_BooleanLiteral(self, expr: BooleanLiteral):
        return expr.value

    def visit_NullLiteral(self, expr: NullLiteral):
        return None

    def visit_Identifier(self, expr: Identifier):
        return self.environment.get(expr.value, expr)

    def visit_ListLiteral(self, expr: ListLiteral):
        return [self.evaluate(el) for el in expr.elements]

    def visit_DictLiteral(self, expr: DictLiteral):
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
