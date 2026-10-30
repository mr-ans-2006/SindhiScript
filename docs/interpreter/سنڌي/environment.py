# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Environment & Lexical Scoping
"""
from typing import Any, Dict, Optional


from .errors import RuntimeError


class Environment:
    def __init__(self, enclosing: Optional['Environment'] = None):
        self.enclosing = enclosing
        self.values: Dict[str, Any] = {}
        self.constants: set = set()

    def define(self, name: str, value: Any, is_const: bool = False):
        if name in self.values:
            raise RuntimeError(f"متغير '{name}' اڳ ۾ ئي موجود آهي", None)
        self.values[name] = value
        if is_const:
            self.constants.add(name)

    def assign(self, name: str, value: Any, node=None):
        if name in self.values:
            if name in self.constants:
                raise RuntimeError(f"ثابت '{name}' کي ٻيهر قيمت ڏئي نٿي سگهجي", node)
            self.values[name] = value
            return
        
        if self.enclosing is not None:
            self.enclosing.assign(name, value, node)
            return

        raise RuntimeError(f"اڻ سڃاتل متغير '{name}'", node)

    def get(self, name: str, node=None) -> Any:
        if name in self.values:
            return self.values[name]

        if self.enclosing is not None:
            return self.enclosing.get(name, node)

        raise RuntimeError(f"اڻ سڃاتل متغير '{name}'", node)
