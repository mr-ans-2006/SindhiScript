# سنڌي (SindhiScript)

SindhiScript is a fully functional, tree-walking interpreted programming language that uses the native Sindhi-Arabic script for its keywords, operators, and syntax. It is designed from the ground up to support Right-To-Left (RTL) editing, seamless integration with Python (via FFI), and a complete object-oriented system.

سنڌي اسڪرپٽ هڪ مڪمل طور تي ڪم ڪندڙ، ٽري-واڪنگ انٽرپريٽيڊ پروگرامنگ ٻولي آهي، جيڪا پنهنجي لفظن، آپريٽرز ۽ نحو (syntax) لاءِ نج سنڌي-عربي رسم الخط استعمال ڪري ٿي. هن کي خاص طور تي ساڄي کان کاٻي (RTL) لکڻ، پائيٿون سان سڌي ريت ڳنڍڻ، ۽ مڪمل آبجيڪٽ اورينٽيڊ (OOP) نظام ڏيڻ لاءِ ٺاهيو ويو آهي.

## 🚀 خصوصيتون (Features)

- **100% Native Sindhi Syntax**: Write code using words like `متغير` (var), `طبقو` (class), and `جيڪڏهن` (if).
  - **100٪ نج سنڌي نحو**: پنهنجو ڪوڊ نج سنڌي لفظن جهڙوڪ `متغير`، `طبقو`، ۽ `جيڪڏهن` استعمال ڪندي لکو.
- **Python FFI (`ٻاهري ڪم`)**: Directly embed and execute raw Python code inside your Sindhi functions.
  - **پائيٿون سان ڳانڍاپو**: پنهنجي سنڌي ڪمن (functions) ۾ پائيٿون جو اصلي ڪوڊ سڌو لکو ۽ هلايو.
- **Object-Oriented**: Full support for classes (`طبقو`) and single inheritance (`ورثو`).
  - **آبجيڪٽ اورينٽيڊ**: طبقن (classes) ۽ ورثي (inheritance) لاءِ مڪمل سهولت.
- **Rich Standard Library**: Built-in math, file IO, and string manipulation using Sindhi equivalents of Python functions.
  - **بھترين معياري لئبرري**: رياضي، فائل پڙهڻ/لکڻ ۽ لفظن کي سنڀالڻ جا بلٽ-ان فنڪشن.
- **Robust Error Handling**: Sindhi-translated exceptions with exact line and column numbers.
  - **غلطين جي نشاندهي**: غلطين کي سندن درست سٽ ۽ ڪالم نمبر سان سنڌيءَ ۾ ظاهر ڪرڻ.
- **Terminal Fallback**: A `.رومن` command to automatically transliterate Sindhi output to Latin letters for systems without proper RTL font support.
  - **رومن ترجمو**: جن سسٽمن تي سنڌي فونٽ ڪم نٿا ڪن، تن لاءِ `.رومن` جي ڪمانڊ استعمال ڪريو.

## 🛠️ انسٽاليشن (Installation)

## 🛠️ انسٽاليشن (Installation)

Getting started with SindhiScript is incredibly simple. It requires zero external dependencies, just Python itself!

*سنڌي اسڪرپٽ سان شروعات ڪرڻ انتهائي آسان آهي. ان لاءِ ڪنهن ٻئي سافٽويئر جي ضرورت ناهي، رڳو پائيٿون جو هجڻ لازمي آهي!*

1. Clone this repository to your computer:
   *(پنهنجي ڪمپيوٽر تي هي ريپازيٽري ڪلون ڪريو):*
   ```bash
   git clone https://github.com/mr-ans-2006/SindhiScript.git
   cd SindhiScript
   ```

2. Ensure you have **Python 3.8+** installed on your system.
   *(پڪ ڪريو ته توهان جي ڪمپيوٽر تي **پائيٿون (Python) 3.8+** انسٽال ٿيل آهي).*

## 📦 ڪيئن هلاجي (How to Run)

### 1. ويب آئي ڊي اي (Web IDE - Recommended / تجويز ڪيل)
Because standard terminals (like VS Code or CMD) struggle to shape and connect Arabic/Sindhi letters properly from Right-To-Left, the best way to write SindhiScript is using the custom built-in Web IDE.
ڇاڪاڻ ته عام ٽرمينل (جهڙوڪ VS Code يا CMD) سنڌي اکرن کي ساڄي کان کاٻي ڳنڍڻ ۽ سهي ڏيکارڻ ۾ ڏکيائي محسوس ڪن ٿا، تنهنڪري سنڌي اسڪرپٽ لکڻ جو بهترين طريقو اسان جي ٺاهيل 'ويب آئي ڊي اي' (Web IDE) جو استعمال آهي.

To launch it / هن کي هلائڻ لاءِ:
```cmd
python web_ide.py
```
Then open your browser to **http://localhost:5000**. You can write multi-line code and press **Ctrl+Enter** to execute it instantly.
پوءِ پنهنجي برائوزر تي **http://localhost:5000** کوليو. اتي توهان گهڻيون سٽون لکي **Ctrl+Enter** دٻائيندي ئي ڪوڊ هلائي سگهو ٿا.

### 2. انٽرايڪٽو موڊ (Interactive REPL)
If you prefer the command line, you can launch the REPL directly:
جيڪڏهن توهان ڪمانڊ لائين استعمال ڪرڻ چاهيو ٿا، ته REPL سڌو به هلائي سگهجي ٿو:
```cmd
python -m سنڌي
```
Inside the REPL, press `Enter` for a new line, and `Alt+Enter` to execute. You can type `.مدد` for help or `.رومن` to toggle Latin fallback mode.
REPL جي اندر نئين سٽ لاءِ `Enter` دٻايو ۽ ڪوڊ هلائڻ لاءِ `Alt+Enter` دٻايو. مدد لاءِ `.مدد` لکو.

### 3. اسڪرپٽ هلائڻ (Running a Script)
You can run any `.سن` script:
توهان ڪنهن به `.سن` فائل کي ائين هلائي سگهو ٿا:
```cmd
python -m سنڌي examples/سنسار.سن
```

### 4. جھنڊا (Flags)
- `--مدد` : Show help menu (مدد ڏيکاريو)
- `--نسخو` : Show version (نسخو ڏيکاريو)
- `--رومن` : Force all output to be transliterated into Roman Sindhi (پروگرام جي سموري نتيجي کي رومن سنڌيءَ ۾ بدلايو)
- `--فونٽ_جانچ` : Run a system diagnostic to check for installed Sindhi fonts (توهان جي سسٽم جا سنڌي فونٽ چيڪ ڪرڻ لاءِ)

## 📚 ڊاڪيومينٽيشن (Documentation)
- [شروعاتي گائيڊ (Getting Started)](docs/شروعات.md)
- [رومن ترجمو (Roman Transliteration)](docs/رومن_ترجمو.md)
- [ٻوليءَ جو حوالو (Language Reference)](docs/حوالو.md)

## 💡 مثال (Example)

See the full working example in [examples/سنسار.سن](examples/سنسار.سن).
مڪمل هلندڙ مثال لاءِ [examples/سنسار.سن](examples/سنسار.سن) ڏسو.

```sindhi
ڇاپ("--- سنڌي پروگرامنگ جي دنيا ۾ ڀليڪار ---")

متغير نالو = "سنسار"
ڇاپ("نالو: "، نالو)

طبقو جانور:
    ڪم پيدائش(نالو، عمر):
        پنهنجو.نالو = نالو
        پنهنجو.عمر = عمر

متغير طوطو = جانور("مٺو طوطو"، 2)
ڇاپ("پکي جو نالو: "، طوطو.نالو)
```
