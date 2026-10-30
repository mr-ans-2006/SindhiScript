# -*- coding: utf-8 -*-
"""
سنڌي (SindhiScript) — Parser

Recursive descent parser mapping a stream of Token objects into an AST.
"""
from typing import List, Optional

from .tokenizer import Token, TokenType
from .ast_nodes import *


from .errors import ParseError


class Parser:
    def __init__(self, tokens: List[Token], filename: str = '<stdin>'):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]  # EOF token
        return self.tokens[idx]

    def _previous(self) -> Token:
        return self.tokens[self.pos - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, ttype: TokenType, value: Optional[str] = None) -> bool:
        if self._is_at_end():
            return False
        token = self._peek()
        if token.type != ttype:
            return False
        if value is not None and token.value != value:
            return False
        return True

    def _match(self, ttype: TokenType, value: Optional[str] = None) -> bool:
        if self._check(ttype, value):
            self.pos += 1
            return True
        return False

    def _consume(self, ttype: TokenType, message: str, value: Optional[str] = None) -> Token:
        if self._check(ttype, value):
            self.pos += 1
            return self._previous()
        raise ParseError(message, self._peek(), self.filename)

    def _match_any_operator(self, *operators) -> bool:
        for op in operators:
            if self._check(TokenType.OPERATOR, op):
                self.pos += 1
                return True
        return False

    def _skip_newlines(self):
        while self._match(TokenType.NEWLINE):
            pass

    # ─── PARSER ENTRY ────────────────────────────────────────────────────────

    def parse(self) -> Program:
        statements = []
        self._skip_newlines()
        while not self._is_at_end():
            statements.append(self._declaration())
            self._skip_newlines()
        return Program(statements)

    # ─── STATEMENTS ─────────────────────────────────────────────────────────

    def _declaration(self) -> Statement:
        try:
            if self._match(TokenType.KEYWORD, 'متغير'):
                return self._var_declaration(is_const=False)
            if self._match(TokenType.KEYWORD, 'ثابت'):
                return self._var_declaration(is_const=True)
            if self._match(TokenType.KEYWORD, 'ڪم'):
                return self._function_declaration(is_extern=False)
            if self._match(TokenType.KEYWORD, 'ٻاهري'):
                self._consume(TokenType.KEYWORD, "ٻاهري کان پوءِ 'ڪم' جي ضرورت آهي", 'ڪم')
                return self._function_declaration(is_extern=True)
            if self._match(TokenType.KEYWORD, 'طبقو'):
                return self._class_declaration()
            return self._statement()
        except ParseError as e:
            # Simple panic mode recovery: skip to next newline
            self._synchronize()
            raise e

    def _var_declaration(self, is_const: bool) -> Statement:
        name_token = self._consume(TokenType.IDENTIFIER, "متغير جو نالو متوقع آهي")
        self._consume(TokenType.SYMBOL, "متغير جي نالي کان پوءِ '=' متوقع آهي", '=')
        initializer = self._expression()
        self._consume(TokenType.NEWLINE, "بيان کان پوءِ نئين سٽ متوقع آهي")
        return VarDecl(name_token.value, initializer, is_const, name_token.line, name_token.column)

    def _function_declaration(self, is_extern: bool) -> Statement:
        name_token = self._consume(TokenType.IDENTIFIER, "ڪم جو نالو متوقع آهي")
        self._consume(TokenType.SYMBOL, "ڪم جي نالي کان پوءِ '(' متوقع آهي", '(')
        
        params = []
        if not self._check(TokenType.SYMBOL, ')'):
            while True:
                param = self._consume(TokenType.IDENTIFIER, "پيراميٽر جو نالو متوقع آهي")
                params.append(param.value)
                if not self._match(TokenType.SYMBOL, '،'):
                    break
        self._consume(TokenType.SYMBOL, "پيراميٽرز کان پوءِ ')' متوقع آهي", ')')
        self._consume(TokenType.SYMBOL, "ڪم جي تعريف کان پوءِ ':' متوقع آهي", ':')
        self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")

        if is_extern:
            # We expect INDENT, RAW_PYTHON, DEDENT
            self._consume(TokenType.INDENT, "ٻاهري ڪم جي بلاڪ لاءِ خالي جاءِ متوقع آهي")
            raw_token = self._consume(TokenType.RAW_PYTHON, "ٻاهري ڪم ۾ پائيٿون ڪوڊ متوقع آهي")
            self._consume(TokenType.DEDENT, "ٻاهري ڪم جو بلاڪ ختم نه ٿيو")
            # Create a block with a single ExternBlockNode
            body_block = Block([ExternBlockNode(raw_token.value, raw_token.line, raw_token.column)], raw_token.line, raw_token.column)
        else:
            body_block = self._block()
            
        return FunctionDecl(name_token.value, params, body_block, is_extern, name_token.line, name_token.column)

    def _class_declaration(self) -> Statement:
        name_token = self._consume(TokenType.IDENTIFIER, "طبقي جو نالو متوقع آهي")
        superclass = None
        if self._match(TokenType.KEYWORD, 'ورثو'):
            super_token = self._consume(TokenType.IDENTIFIER, "ورثي لاءِ طبقي جو نالو متوقع آهي")
            superclass = super_token.value
            
        self._consume(TokenType.SYMBOL, "طبقي جي تعريف کان پوءِ ':' متوقع آهي", ':')
        self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
        
        self._consume(TokenType.INDENT, "طبقي جي بلاڪ لاءِ خالي جاءِ متوقع آهي")
        methods = []
        while not self._check(TokenType.DEDENT) and not self._is_at_end():
            if self._match(TokenType.NEWLINE):
                continue
            self._consume(TokenType.KEYWORD, "طبقي ۾ صرف 'ڪم' (طريقا) ڏئي سگهجن ٿا", 'ڪم')
            methods.append(self._function_declaration(is_extern=False))
        self._consume(TokenType.DEDENT, "طبقي جو بلاڪ ختم نه ٿيو")
        
        return ClassDecl(name_token.value, superclass, methods, name_token.line, name_token.column)

    def _statement(self) -> Statement:
        if self._match(TokenType.KEYWORD, 'جيڪڏهن'):
            return self._if_statement()
        if self._match(TokenType.KEYWORD, 'جڏهن_تائين'):
            return self._while_statement()
        if self._match(TokenType.KEYWORD, 'هر'):
            return self._for_statement()
        if self._match(TokenType.KEYWORD, 'موٽايو'):
            return self._return_statement()
        if self._match(TokenType.KEYWORD, 'ٽوڙيو'):
            return self._break_statement()
        if self._match(TokenType.KEYWORD, 'جاري'):
            return self._continue_statement()
        if self._match(TokenType.KEYWORD, 'ڪوشش'):
            return self._try_statement()
        if self._match(TokenType.KEYWORD, 'آندو'):
            return self._import_statement()
        if self._match(TokenType.KEYWORD, 'مان'):
            return self._from_import_statement()
        if self._match(TokenType.KEYWORD, 'جاريات'):
            return self._export_statement()

        return self._expression_statement()

    def _import_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        module = self._consume(TokenType.IDENTIFIER, "ماڊيول جو نالو متوقع آهي")
        self._consume(TokenType.NEWLINE, "بيان کان پوءِ نئين سٽ متوقع آهي")
        return ImportStmt(module.value, line, col)

    def _from_import_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        module = self._consume(TokenType.IDENTIFIER, "ماڊيول جو نالو متوقع آهي")
        self._consume(TokenType.KEYWORD, "'مان' بيان ۾ 'آندو' متوقع آهي", 'آندو')
        names = []
        while True:
            name = self._consume(TokenType.IDENTIFIER, "نالو متوقع آهي")
            names.append(name.value)
            if not self._match(TokenType.SYMBOL, '،'):
                break
        self._consume(TokenType.NEWLINE, "بيان کان پوءِ نئين سٽ متوقع آهي")
        return FromImportStmt(module.value, names, line, col)

    def _export_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        names = []
        while True:
            name = self._consume(TokenType.IDENTIFIER, "نالو متوقع آهي")
            names.append(name.value)
            if not self._match(TokenType.SYMBOL, '،'):
                break
        self._consume(TokenType.NEWLINE, "بيان کان پوءِ نئين سٽ متوقع آهي")
        return ExportStmt(names, line, col)

    def _if_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        condition = self._expression()
        self._consume(TokenType.SYMBOL, "شرط کان پوءِ ':' متوقع آهي", ':')
        self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
        then_branch = self._block()

        elif_branches = []
        while self._match(TokenType.KEYWORD, 'ٻي_صورت'):
            elif_cond = self._expression()
            self._consume(TokenType.SYMBOL, "شرط کان پوءِ ':' متوقع آهي", ':')
            self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
            elif_block = self._block()
            elif_branches.append((elif_cond, elif_block))

        else_branch = None
        if self._match(TokenType.KEYWORD, 'نه_ته'):
            self._consume(TokenType.SYMBOL, "'نه_ته' کان پوءِ ':' متوقع آهي", ':')
            self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
            else_branch = self._block()

        return IfStmt(condition, then_branch, elif_branches, else_branch, line, col)

    def _while_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        condition = self._expression()
        self._consume(TokenType.SYMBOL, "شرط کان پوءِ ':' متوقع آهي", ':')
        self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
        body = self._block()
        return WhileStmt(condition, body, line, col)

    def _for_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        item_name = self._consume(TokenType.IDENTIFIER, "'هر' کان پوءِ متغير جو نالو متوقع آهي").value
        self._consume(TokenType.OPERATOR, "متغير کان پوءِ '۾' متوقع آهي", '۾')
        iterable = self._expression()
        self._consume(TokenType.SYMBOL, "لوپ جي تعريف کان پوءِ ':' متوقع آهي", ':')
        self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
        body = self._block()
        return ForStmt(item_name, iterable, body, line, col)

    def _try_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        self._consume(TokenType.SYMBOL, "'ڪوشش' کان پوءِ ':' متوقع آهي", ':')
        self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
        try_block = self._block()

        catch_name = None
        catch_block = None
        if self._match(TokenType.KEYWORD, 'غلطي'):
            if self._check(TokenType.IDENTIFIER):
                catch_name = self._consume(TokenType.IDENTIFIER, "").value
            self._consume(TokenType.SYMBOL, "'غلطي' کان پوءِ ':' متوقع آهي", ':')
            self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
            catch_block = self._block()

        finally_block = None
        if self._match(TokenType.KEYWORD, 'آخر'):
            self._consume(TokenType.SYMBOL, "'آخر' کان پوءِ ':' متوقع آهي", ':')
            self._consume(TokenType.NEWLINE, "':' کان پوءِ نئين سٽ متوقع آهي")
            finally_block = self._block()

        if not catch_block and not finally_block:
            raise ParseError("'ڪوشش' سان گڏ گهٽ ۾ گهٽ هڪ 'غلطي' يا 'آخر' بلاڪ هجڻ گهرجي", self._previous(), self.filename)

        return TryStmt(try_block, catch_name, catch_block, finally_block, line, col)

    def _return_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        value = None
        if not self._check(TokenType.NEWLINE):
            value = self._expression()
        self._consume(TokenType.NEWLINE, "بيان کان پوءِ نئين سٽ متوقع آهي")
        return ReturnStmt(value, line, col)

    def _break_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        self._consume(TokenType.NEWLINE, "بيان کان پوءِ نئين سٽ متوقع آهي")
        return BreakStmt(line, col)

    def _continue_statement(self) -> Statement:
        line, col = self._previous().line, self._previous().column
        self._consume(TokenType.NEWLINE, "بيان کان پوءِ نئين سٽ متوقع آهي")
        return ContinueStmt(line, col)

    def _expression_statement(self) -> Statement:
        expr = self._expression()
        self._consume(TokenType.NEWLINE, "بيان کان پوءِ نئين سٽ متوقع آهي")
        return ExpressionStatement(expr, expr.line, expr.col)

    def _block(self) -> Block:
        self._consume(TokenType.INDENT, "بلاڪ لاءِ خالي جاءِ (انڊينٽيشن) متوقع آهي")
        statements = []
        line, col = self._previous().line, self._previous().column
        while not self._check(TokenType.DEDENT) and not self._is_at_end():
            if self._match(TokenType.NEWLINE):
                continue
            statements.append(self._declaration())
        self._consume(TokenType.DEDENT, "بلاڪ جو انڊينٽيشن ختم نه ٿيو")
        return Block(statements, line, col)

    # ─── EXPRESSIONS ────────────────────────────────────────────────────────

    def _expression(self) -> Expression:
        return self._assignment()

    def _assignment(self) -> Expression:
        expr = self._logical_or()

        if self._match(TokenType.SYMBOL, '='):
            equals = self._previous()
            value = self._assignment()
            
            if isinstance(expr, (Identifier, MemberAccess, IndexAccess)):
                return Assignment(expr, value, equals.line, equals.column)
            
            raise ParseError("غير قانوني اسائنمينٽ ٽارگيٽ", equals, self.filename)

        return expr

    def _logical_or(self) -> Expression:
        expr = self._logical_and()
        while self._match(TokenType.OPERATOR, 'يا'):
            op = self._previous().value
            right = self._logical_and()
            expr = BinaryOp(expr, op, right, expr.line, expr.col)
        return expr

    def _logical_and(self) -> Expression:
        expr = self._equality()
        while self._match(TokenType.OPERATOR, '۽'):
            op = self._previous().value
            right = self._equality()
            expr = BinaryOp(expr, op, right, expr.line, expr.col)
        return expr

    def _equality(self) -> Expression:
        expr = self._comparison()
        while self._match_any_operator('برابر', 'نه_برابر'):
            op = self._previous().value
            right = self._comparison()
            expr = BinaryOp(expr, op, right, expr.line, expr.col)
        return expr

    def _comparison(self) -> Expression:
        expr = self._term()
        while self._match_any_operator('وڌيڪ', 'گهٽ', 'وڌيڪ_برابر', 'گهٽ_برابر', '۾'):
            op = self._previous().value
            right = self._term()
            expr = BinaryOp(expr, op, right, expr.line, expr.col)
        return expr

    def _term(self) -> Expression:
        expr = self._factor()
        while self._match_any_operator('جمع', 'گهٽائڻ'):
            op = self._previous().value
            right = self._factor()
            expr = BinaryOp(expr, op, right, expr.line, expr.col)
        return expr

    def _factor(self) -> Expression:
        expr = self._unary()
        while self._match_any_operator('ضرب', 'تقسيم', 'باقي'):
            op = self._previous().value
            right = self._unary()
            expr = BinaryOp(expr, op, right, expr.line, expr.col)
        return expr

    def _unary(self) -> Expression:
        if self._match_any_operator('نه', 'گهٽائڻ', 'جمع'):
            op = self._previous()
            right = self._unary()
            return UnaryOp(op.value, right, op.line, op.column)
        return self._power()

    def _power(self) -> Expression:
        expr = self._call()
        if self._match(TokenType.OPERATOR, 'طاقت'):
            op = self._previous().value
            right = self._unary()  # power is right-associative usually
            expr = BinaryOp(expr, op, right, expr.line, expr.col)
        return expr

    def _call(self) -> Expression:
        expr = self._primary()

        while True:
            if self._match(TokenType.SYMBOL, '('):
                expr = self._finish_call(expr)
            elif self._match(TokenType.SYMBOL, '.'):
                name = self._consume(TokenType.IDENTIFIER, "نقطي کان پوءِ ملڪيت جو نالو متوقع آهي")
                expr = MemberAccess(expr, name.value, name.line, name.column)
            elif self._match(TokenType.SYMBOL, '['):
                index = self._expression()
                self._consume(TokenType.SYMBOL, "انڊيڪس کان پوءِ ']' متوقع آهي", ']')
                expr = IndexAccess(expr, index, expr.line, expr.col)
            else:
                break
        return expr

    def _finish_call(self, callee: Expression) -> Expression:
        arguments = []
        if not self._check(TokenType.SYMBOL, ')'):
            while True:
                arguments.append(self._expression())
                if not self._match(TokenType.SYMBOL, '،'):
                    break
        paren = self._consume(TokenType.SYMBOL, "آرگيومينٽس کان پوءِ ')' متوقع آهي", ')')
        return Call(callee, arguments, callee.line, callee.col)

    def _primary(self) -> Expression:
        if self._match(TokenType.KEYWORD, 'صحيح'):
            return BooleanLiteral(True, self._previous().line, self._previous().column)
        if self._match(TokenType.KEYWORD, 'غلط'):
            return BooleanLiteral(False, self._previous().line, self._previous().column)
        if self._match(TokenType.KEYWORD, 'ڪجهه_نه'):
            return NullLiteral(self._previous().line, self._previous().column)
            
        if self._match(TokenType.NUMBER):
            num = self._previous()
            val_str = num.value
            val = float(val_str) if '.' in val_str else int(val_str)
            return NumberLiteral(val, num.line, num.column)
            
        if self._match(TokenType.STRING):
            return StringLiteral(self._previous().value, False, self._previous().line, self._previous().column)
            
        if self._match(TokenType.FSTRING):
            return StringLiteral(self._previous().value, True, self._previous().line, self._previous().column)
            
        if self._match(TokenType.IDENTIFIER):
            return Identifier(self._previous().value, self._previous().line, self._previous().column)

        if self._match(TokenType.KEYWORD, 'پنهنجو'):
            return Identifier('پنهنجو', self._previous().line, self._previous().column)
            
        if self._match(TokenType.SYMBOL, '('):
            expr = self._expression()
            self._consume(TokenType.SYMBOL, "اظهار کان پوءِ ')' متوقع آهي", ')')
            return expr
            
        if self._match(TokenType.SYMBOL, '['):
            elements = []
            if not self._check(TokenType.SYMBOL, ']'):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.SYMBOL, '،'):
                        break
            self._consume(TokenType.SYMBOL, "فهرست جي آخر ۾ ']' متوقع آهي", ']')
            return ListLiteral(elements, self._previous().line, self._previous().column)
            
        if self._match(TokenType.SYMBOL, '{'):
            keys = []
            values = []
            if not self._check(TokenType.SYMBOL, '}'):
                while True:
                    keys.append(self._expression())
                    self._consume(TokenType.SYMBOL, "لغت ۾ ڪنجي کان پوءِ ':' متوقع آهي", ':')
                    values.append(self._expression())
                    if not self._match(TokenType.SYMBOL, '،'):
                        break
            self._consume(TokenType.SYMBOL, "لغت جي آخر ۾ '}' متوقع آهي", '}')
            return DictLiteral(keys, values, self._previous().line, self._previous().column)

        raise ParseError("اظهار متوقع آهي", self._peek(), self.filename)

    def _synchronize(self):
        self.pos += 1
        while not self._is_at_end():
            if self._previous().type == TokenType.NEWLINE:
                return
            if self._peek().type == TokenType.KEYWORD and self._peek().value in (
                'متغير', 'ثابت', 'ڪم', 'طبقو', 'جيڪڏهن', 'هر', 'جڏهن_تائين', 'موٽايو', 'ڪوشش'
            ):
                return
            self.pos += 1
