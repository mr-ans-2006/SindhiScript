# سنڌي — SindhiScript

**A programming language written in Sindhi.** SindhiScript is a tree-walking interpreter, written in Python, whose keywords, operators and built-in functions are all Sindhi words in the Sindhi-Arabic script.

> سنڌي اسڪرپٽ هڪ پروگرامنگ ٻولي آهي جنهن جا سڀ لفظ، آپريٽر ۽ فنڪشن سنڌي ۾ آهن.

```
ڪم سلام_ڪريو(نالو):
    ڇاپ("سلام،"، نالو)

سلام_ڪريو("سنڌ")
```

---

## What's inside

The interpreter is a classic pipeline, built from scratch with no parser generators:

| Stage | File | What it does |
|---|---|---|
| Lexer | `سنڌي/lexer.py` | Turns UTF-8 source into tokens. Handles Python-style indentation (INDENT/DEDENT), Sindhi and Western digits, and blocks invisible characters from being used to spoof identifiers |
| Parser | `سنڌي/parser.py` | Recursive-descent parser that builds an AST (`سنڌي/ast_nodes.py`) |
| Evaluator | `سنڌي/evaluator.py` | Walks the AST, with lexical scopes and closures (`environment.py`) |
| Standard library | `سنڌي/stdlib.py` | Built-in functions with Sindhi names |
| Modules | `سنڌي/module_loader.py` | `آندو` / `مان … آندو` imports from other `.سن` files |
| Errors | `سنڌي/errors.py` | Error messages in Sindhi, with file, line and column |
| REPL & CLI | `سنڌي/repl.py`, `سنڌي/__main__.py` | Interactive shell and script runner |
| Web IDE | `web_ide.py`, `web_ide.html` | Browser editor with proper right-to-left rendering |

## Features

- **Variables and constants:** `متغير` and `ثابت`. Reassigning a constant is a runtime error.
- **Data types:** integers, floats, strings, booleans (`صحيح` / `غلط`), null (`ڪجهه_نه`), lists `[…]` and dictionaries `{…}`.
- **f-strings:** `f"سلام {نالو}، عمر {عمر جمع 1}"` fills in any expression, and Python format specs work too (`f"{قدر:.2f}"`).
- **Sindhi digits:** `۱۲ جمع ۳` works the same as `12 جمع 3`.
- **Word operators:** arithmetic, comparison and logic are written as Sindhi words (`جمع`, `ضرب`, `برابر`, `۽`, `يا` …). See the table below.
- **Control flow:** `جيڪڏهن` / `ٻي_صورت` / `نه_ته` (if / elif / else), `جڏهن_تائين` (while), `هر … ۾ …` (for-each), `ٽوڙيو` (break), `جاري` (continue).
- **Functions:** `ڪم` with parameters, `موٽايو` (return), recursion and closures.
- **Classes:** `طبقو` with a `پيدائش` constructor, `پنهنجو` (self), methods and single inheritance with `ورثو`.
- **Error handling:** `ڪوشش` / `غلطي` / `آخر` (try / except / finally). Division by zero, bad types, out-of-range indexes and so on become catchable errors.
- **Modules:** `آندو اوزار` or `مان اوزار آندو چورس`, with `جاريات` to choose what a module exports.
- **Python interop:** a `ٻاهري ڪم` block holds raw Python, so you can call any Python library from SindhiScript.
- **Roman fallback:** `--رومن` transliterates output to Latin letters for terminals that can't shape Arabic script.
- **Indentation-based blocks**, like Python, and `#` comments.

## Getting started

You need **Python 3.8+**.

```bash
git clone https://github.com/mr-ans-2006/SindhiScript.git
cd SindhiScript
```

Run a script (no install needed):

```bash
python -m سنڌي examples/سنسار.سن
```

Or install it, which gives you a `sindhiscript` command:

```bash
pip install .
sindhiscript examples/سنسار.سن
```

`pip install .` also installs `prompt_toolkit`, which the interactive REPL uses.

### Three ways to write code

1. **Web IDE (recommended).** Most terminals can't join Sindhi letters right to left, so a browser is the most comfortable place to write it.
   ```bash
   python web_ide.py
   ```
   Open http://localhost:5000, write your code and press **Ctrl+Enter** to run it. `داخل_ڪرو` (input) works in the browser too. Run this from the repo folder.
   The IDE runs whatever code it receives, including raw Python, so it only listens on your own computer (`127.0.0.1`). To open it to your network on purpose, run `python web_ide.py --عام` (or set `SINDHI_IDE_PUBLIC=1`). Only do that on a network you trust.
2. **REPL:** `python -m سنڌي`. Press **Enter** for a new line and **Alt+Enter** to run. Type `.مدد` for help and `.رومن` to toggle Roman output.
3. **Script files:** save code as `something.سن` (UTF-8) and run `python -m سنڌي something.سن`.

### Command-line flags

| Flag | Meaning |
|---|---|
| `--مدد` | Help |
| `--نسخو` | Version |
| `--رومن` | Transliterate all output to Roman (Latin) letters |
| `--فونٽ_جانچ` | Check whether your terminal has Sindhi fonts |

## Examples

Every example below was run with `python -m سنڌي`, and the output shown is what the interpreter actually printed.

### 1. Variables, constants and types

```
# متغير ۽ ثابت
متغير نالو = "علي"
ثابت سال = 2026
ڇاپ("سلام،"، نالو)
ڇاپ("سال:"، سال)
ڇاپ("ڊگهائي:"، ڊگھائي(نالو))
ڇاپ(قسم(سال)، قسم(3.5)، قسم("متن")، قسم(صحيح))
```

Output:

```text
سلام، علي
سال: 2026
ڊگهائي: 3
عدد اعشاري متن صحيح/غلط
```

### 2. Conditions and loops: FizzBuzz

```
# FizzBuzz سنڌي ۾
هر ع ۾ حد(1، 16):
    جيڪڏهن ع باقي 15 برابر 0:
        ڇاپ("فِزبَز")
    ٻي_صورت ع باقي 3 برابر 0:
        ڇاپ("فِز")
    ٻي_صورت ع باقي 5 برابر 0:
        ڇاپ("بَز")
    نه_ته:
        ڇاپ(ع)
```

Output:

```text
1
2
فِز
4
بَز
فِز
7
8
فِز
بَز
11
فِز
13
14
فِزبَز
```

### 3. Recursion, while loops and lists

```
ڪم فبوناچي(ن):
    جيڪڏهن ن گهٽ 2:
        موٽايو ن
    موٽايو فبوناچي(ن گهٽائڻ 1) جمع فبوناچي(ن گهٽائڻ 2)

متغير نتيجا = []
متغير ع = 0
جڏهن_تائين صحيح:
    جيڪڏهن ع وڌيڪ_برابر 10:
        ٽوڙيو
    شامل_ڪرو(نتيجا، فبوناچي(ع))
    ع = ع جمع 1
ڇاپ(نتيجا)
ڇاپ("مجموعو:"، مجموعو(نتيجا))
```

Output:

```text
[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
مجموعو: 88
```

### 4. Dictionaries and `۾` (in)

```
متغير نمبر = {"علي": 85، "سارا": 92، "احمد": 78}
نمبر["زينب"] = 88

هر نالو ۾ نمبر:
    جيڪڏهن نمبر[نالو] وڌيڪ_برابر 85:
        ڇاپ(نالو، "پاس (A)")
    نه_ته:
        ڇاپ(نالو، "پاس")

ڇاپ("سڀ کان وڌيڪ:"، وڌ_ٽو_وڌ([85، 92، 78، 88]))
ڇاپ("زينب" ۾ نمبر، "حامد" ۾ نمبر)
```

Output:

```text
علي پاس (A)
سارا پاس (A)
احمد پاس
زينب پاس (A)
سڀ کان وڌيڪ: 92
صحيح غلط
```

### 5. Classes and inheritance

```
طبقو کاتو:
    ڪم پيدائش(مالڪ، رقم):
        پنهنجو.مالڪ = مالڪ
        پنهنجو.رقم = رقم

    ڪم وڌايو(ر):
        پنهنجو.رقم = پنهنجو.رقم جمع ر
        موٽايو پنهنجو.رقم

طبقو بچت_کاتو ورثو کاتو:
    ڪم منافعو(شرح):
        موٽايو پنهنجو.رقم ضرب شرح تقسيم 100

متغير ک = بچت_کاتو("علي"، 1000)
ڇاپ(ک.مالڪ، "جي رقم:"، ک.وڌايو(500))
ڇاپ("منافعو:"، ک.منافعو(5))
```

Output:

```text
علي جي رقم: 1500
منافعو: 75.0
```

### 6. Error handling

```
ڪوشش:
    متغير ن = 10 تقسيم 0
غلطي خ:
    ڇاپ("غلطي پڪڙي وئي!")
آخر:
    ڇاپ("هي هميشه هلندو آهي")
```

Output:

```text
غلطي پڪڙي وئي!
هي هميشه هلندو آهي
```

### 7. Calling Python

Inside a `ٻاهري ڪم` the body is plain Python. `math`, `time` and `random` are already available.

```
ٻاهري ڪم فيڪٽوريل(ن):
    return math.factorial(ن)

ٻاهري ڪم وڏا_اکر(لفظ):
    return لفظ.upper()

ڇاپ("20! ="، فيڪٽوريل(20))
ڇاپ(وڏا_اکر("sindhiscript"))
```

Output:

```text
20! = 2432902008176640000
SINDHISCRIPT
```

### 8. Modules

`اوزار.سن`:

```
ڪم چورس(ن):
    موٽايو ن ضرب ن

ثابت پائي = 3.14159
```

`ماڊيول.سن`, in the same folder:

```
آندو اوزار
ڇاپ(اوزار.چورس(7))

مان اوزار آندو چورس، پائي
ڇاپ(پائي ضرب چورس(2))
```

Output:

```text
49
12.56636
```

The bigger tour in [`examples/سنسار.سن`](examples/سنسار.سن) covers variables, functions, loops, lists, classes and Python interop in one file.

## Keyword reference

### Keywords

| Sindhi | English | Notes |
|---|---|---|
| `متغير` | let / var | `متغير ن = 5` |
| `ثابت` | const | can't be reassigned |
| `ڪم` | def / function | |
| `موٽايو` | return | |
| `طبقو` | class | |
| `ورثو` | extends / inherits | `طبقو پکي ورثو جانور:` |
| `پنهنجو` | self / this | |
| `پيدائش` | constructor (`__init__`) | a method name, not a keyword |
| `جيڪڏهن` | if | |
| `ٻي_صورت` | elif / else if | |
| `نه_ته` | else | |
| `جڏهن_تائين` | while | |
| `هر` | for (each) | `هر ميوو ۾ ميوا:` |
| `ٽوڙيو` | break | |
| `جاري` | continue | |
| `ڪوشش` | try | |
| `غلطي` | except / catch | `غلطي خ:` binds the message |
| `آخر` | finally | |
| `صحيح` | true | |
| `غلط` | false | |
| `ڪجهه_نه` | null / None | |
| `آندو` | import | |
| `مان` | from | `مان اوزار آندو چورس` |
| `جاريات` | export | |
| `ٻاهري` | extern (Python block) | `ٻاهري ڪم …:` |
| `نئون` | new | reserved, not used yet |

### Operators

| Sindhi | Symbol | Meaning |
|---|---|---|
| `جمع` | `+` | add / join strings |
| `گهٽائڻ` | `-` | subtract / negate |
| `ضرب` | `*` | multiply |
| `تقسيم` | `/` | divide |
| `باقي` | `%` | remainder |
| `طاقت` | `**` | power |
| `برابر` | `==` | equal |
| `نه_برابر` | `!=` | not equal |
| `وڌيڪ` | `>` | greater than |
| `گهٽ` | `<` | less than |
| `وڌيڪ_برابر` | `>=` | greater or equal |
| `گهٽ_برابر` | `<=` | less or equal |
| `۽` | `and` | logical and |
| `يا` | `or` | logical or |
| `نه` | `not` | logical not |
| `۾` | `in` | membership / for-each |

Separate items with the Sindhi comma `،`. A plain `,` works too and means the same thing.

### Built-in functions

| Sindhi | Python equivalent |
|---|---|
| `ڇاپ` | `print` |
| `داخل_ڪرو` | `input` |
| `عدد`, `اعشاري`, `متن` | `int`, `float`, `str` |
| `فهرست`, `لغت`, `سيٽ` | `list`, `dict`, `set` |
| `قسم` | type name in Sindhi (`عدد`, `متن`, …) |
| `ڊگھائي` | `len` |
| `حد` | `range` (returns a list) |
| `شامل_ڪرو`, `هٽايو`, `گڏ_ڪرو` | `list.append`, `list.remove`, `list.extend` |
| `ٽڪرا_ڪرو`, `ڳنڍيو`, `ترجمو_ڪرو` | `str.split`, `str.join`, `str.replace` |
| `ڪوپي_ڪرو` | `copy.deepcopy` |
| `فائل_پڙهيو`, `فائل_لکيو` | read / write a UTF-8 file |
| `جذر`, `قوت_ڪرو`, `قدر_مطلق`, `گول` | `sqrt`, `pow`, `abs`, `round` |
| `وڌ_ٽو_وڌ`, `ننڍو_ٽو_ننڍو`, `مجموعو` | `max`, `min`, `sum` |
| `سائن`, `ڪوسائن`, `ٽينجينٽ`, `لگ`, `ايڪسپ` | `sin`, `cos`, `tan`, `log`, `exp` |
| `تصادفي` | `random.random` |
| `وقت`, `تاريخ` | Unix time, current date-time string |
| `سڃاڻپ` | `id` |
| `بند_ڪرو` | `sys.exit` |

## Good to know

- Identifiers must be in Sindhi script, and a name can't contain an operator word as one of its parts. For example, `جمع_ڪرو` is rejected because it contains `جمع`.
- `ھ` (U+06BE) and `ه` (U+0647) are treated as the same letter in names and keywords, so `ڊگھائي` and `ڊگهائي` both work.
- Errors are reported in Sindhi with the file, line and column, and a script that fails exits with code 1.
- Module files are looked up relative to the folder you run the command from.
- `ٻاهري ڪم` runs real Python with full access to your machine, so only run SindhiScript code you trust.

## Docs

- [Getting started (شروعات)](docs/شروعات.md)
- [Roman transliteration (رومن ترجمو)](docs/رومن_ترجمو.md)
- [Language reference (حوالو)](docs/حوالو.md)

## Author

Made by [Ali Nawaz](https://github.com/mr-ans-2006), a CS student from Tharparkar, Sindh.

## License

[MIT](LICENSE)
