# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Standard Library (stdlib)
"""
import sys
import time
import math
import random
from datetime import datetime

from .evaluator import SindhiCallable
from .errors import RuntimeError
from . import terminal


class BuiltinFunction(SindhiCallable):
    def __init__(self, name: str, arity_val: int, func):
        self.name = name
        self._arity = arity_val
        self.func = func

    def arity(self) -> int:
        return self._arity

    def call(self, evaluator, arguments, node=None):
        try:
            return self.func(*arguments)
        except Exception as e:
            raise RuntimeError(f"بِلٽ-اِن فنڪشن '{self.name}' ۾ غلطي: {e}", node)

    def __str__(self):
        return f"<بِلٽ-اِن ڪم {self.name}>"


# ─── I/O ────────────────────────────────────────────────────────────────────

def builtin_print(*args):
    # 'ڇاپ'
    text = " ".join(str(a) for a in args)
    terminal.print_output(text)
    return None

def builtin_input(prompt):
    # 'داخل_ڪرو'
    if terminal.ROMAN_MODE_ENABLED:
        p = terminal.transliterate_to_roman(str(prompt))
        return input(p)
    return input(str(prompt))

# ─── Type Conversions ───────────────────────────────────────────────────────

def builtin_int(val): return int(val)
def builtin_float(val): return float(val)
def builtin_str(val): return str(val)
def builtin_list(val): return list(val)
def builtin_dict(val): return dict(val)
def builtin_set(val): return set(val)
def builtin_type(val):
    t = type(val)
    if t == int: return "عدد"
    if t == float: return "اعشاري"
    if t == str: return "متن"
    if t == list: return "فهرست"
    if t == dict: return "لغت"
    if t == set: return "سيٽ"
    if t == bool: return "صحيح/غلط"
    if val is None: return "ڪجهه_نه"
    return "ٻيو"

# ─── Sequence & Collections ─────────────────────────────────────────────────

def builtin_len(val): return len(val)
def builtin_range(*args): return list(range(*args))
def builtin_append(lst, val): 
    lst.append(val)
    return lst
def builtin_remove(lst, val):
    lst.remove(val)
    return lst
def builtin_extend(lst, other):
    lst.extend(other)
    return lst
def builtin_split(text, sep=None):
    return text.split(sep)
def builtin_join(sep, iterable):
    return sep.join(iterable)
def builtin_replace(text, old, new):
    return text.replace(old, new)
def builtin_copy(obj):
    import copy
    return copy.deepcopy(obj)

# ─── File I/O ───────────────────────────────────────────────────────────────

def builtin_file_read(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def builtin_file_write(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(content))
    return True

# ─── Math & Random ──────────────────────────────────────────────────────────

def builtin_sqrt(val): return math.sqrt(val)
def builtin_pow(base, exp): return math.pow(base, exp)
def builtin_abs(val): return abs(val)
def builtin_round(val, ndigits=None): return round(val, ndigits)
def builtin_max(*args):
    if len(args) == 1 and isinstance(args[0], list):
        return max(args[0])
    return max(args)
def builtin_min(*args):
    if len(args) == 1 and isinstance(args[0], list):
        return min(args[0])
    return min(args)
def builtin_sum(iterable): return sum(iterable)
def builtin_random(): return random.random()
def builtin_sin(val): return math.sin(val)
def builtin_cos(val): return math.cos(val)
def builtin_tan(val): return math.tan(val)
def builtin_log(val): return math.log(val)
def builtin_exp(val): return math.exp(val)

# ─── Time & System ──────────────────────────────────────────────────────────

def builtin_time(): return time.time()
def builtin_date(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def builtin_exit(code=0): sys.exit(code)
def builtin_id(obj): return id(obj)


# ─── Global Environment Setup ───────────────────────────────────────────────

def setup_builtins(env):
    """Register all standard library functions in the global environment."""
    
    # We use -1 arity for varargs (like print, range, max, min)
    # The evaluator will need to bypass arity checks for -1.
    
    builtins = {
        'ڇاپ': BuiltinFunction('ڇاپ', -1, builtin_print),
        'داخل_ڪرو': BuiltinFunction('داخل_ڪرو', 1, builtin_input),
        
        # Types
        'عدد': BuiltinFunction('عدد', 1, builtin_int),
        'اعشاري': BuiltinFunction('اعشاري', 1, builtin_float),
        'متن': BuiltinFunction('متن', 1, builtin_str),
        'فهرست': BuiltinFunction('فهرست', 1, builtin_list),
        'لغت': BuiltinFunction('لغت', 1, builtin_dict),
        'سيٽ': BuiltinFunction('سيٽ', 1, builtin_set),
        'قسم': BuiltinFunction('قسم', 1, builtin_type),
        
        # Sequences
        'ڊگھائي': BuiltinFunction('ڊگھائي', 1, builtin_len),
        'حد': BuiltinFunction('حد', -1, builtin_range),
        'شامل_ڪرو': BuiltinFunction('شامل_ڪرو', 2, builtin_append),
        'هٽايو': BuiltinFunction('هٽايو', 2, builtin_remove),
        'گڏ_ڪرو': BuiltinFunction('گڏ_ڪرو', 2, builtin_extend),
        'ٽڪرا_ڪرو': BuiltinFunction('ٽڪرا_ڪرو', -1, builtin_split), # text, sep
        'ڳنڍيو': BuiltinFunction('ڳنڍيو', 2, builtin_join),
        'ترجمو_ڪرو': BuiltinFunction('ترجمو_ڪرو', 3, builtin_replace),
        'ڪوپي_ڪرو': BuiltinFunction('ڪوپي_ڪرو', 1, builtin_copy),
        
        # Files
        'فائل_پڙهيو': BuiltinFunction('فائل_پڙهيو', 1, builtin_file_read),
        'فائل_لکيو': BuiltinFunction('فائل_لکيو', 2, builtin_file_write),
        
        # Math
        'جذر': BuiltinFunction('جذر', 1, builtin_sqrt),
        'قوت_ڪرو': BuiltinFunction('قوت_ڪرو', 2, builtin_pow),
        'قدر_مطلق': BuiltinFunction('قدر_مطلق', 1, builtin_abs),
        'گول': BuiltinFunction('گول', -1, builtin_round),
        'وڌ_ٽو_وڌ': BuiltinFunction('وڌ_ٽو_وڌ', -1, builtin_max),
        'ننڍو_ٽو_ننڍو': BuiltinFunction('ننڍو_ٽو_ننڍو', -1, builtin_min),
        'مجموعو': BuiltinFunction('مجموعو', 1, builtin_sum),
        'تصادفي': BuiltinFunction('تصادفي', 0, builtin_random),
        'سائن': BuiltinFunction('سائن', 1, builtin_sin),
        'ڪوسائن': BuiltinFunction('ڪوسائن', 1, builtin_cos),
        'ٽينجينٽ': BuiltinFunction('ٽينجينٽ', 1, builtin_tan),
        'لگ': BuiltinFunction('لگ', 1, builtin_log),
        'ايڪسپ': BuiltinFunction('ايڪسپ', 1, builtin_exp),
        
        # Time & Sys
        'وقت': BuiltinFunction('وقت', 0, builtin_time),
        'تاريخ': BuiltinFunction('تاريخ', 0, builtin_date),
        'بند_ڪرو': BuiltinFunction('بند_ڪرو', -1, builtin_exit),
        'سڃاڻپ': BuiltinFunction('سڃاڻپ', 1, builtin_id),
    }
    
    for name, func in builtins.items():
        env.define(name, func, is_const=True)
