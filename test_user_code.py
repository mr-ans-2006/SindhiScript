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
