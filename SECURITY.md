# Security

The live demo (https://mr-ans-2006.github.io/SindhiScript/) runs visitors'
SindhiScript code in their own browser. This file lists the threats that
creates and how the demo defends against each one. The demo's code lives
in `docs/`; its interpreter in `docs/interpreter/سنڌي/` is a copy of the main
package with the limits below added.

## Threat model

- **T1 — Hang:** a visitor writes an infinite loop and freezes their own tab.
- **T2 — Memory blowup:** unbounded list/dict construction, deep recursion,
  giant powers or string/list repetition crash the tab.
- **T3 — Output injection (XSS):** program output contains `<script>` or
  HTML and the page renders it as HTML.
- **T4 — Pyodide surface creep:** the import / Python-interop block reaches
  browser APIs (`js`, `pyodide.http`, `localStorage`, `document`).
- **T5 — Supply chain:** a compromised CDN or version drift in Pyodide;
  tampered bundled `.سن` examples.
- **T6 — Module loader path traversal:** a `.سن` import reads arbitrary
  files from Pyodide's filesystem.

## Defenses

- **T1 — Worker + two limits.** The interpreter runs in `worker.js`, never
  on the UI thread. A step budget (300,000 steps, counted in the
  evaluator's `execute`/`evaluate` dispatch) raises a graceful Sindhi
  "step limit exceeded" error. A 5-second `worker.terminate()` on the UI
  thread is the hard backstop, and Reset starts a fresh worker. An
  infinite loop stops in about 0.6 s.
- **T2 — Collection ceilings + recursion caps.** Lists/dicts are refused
  above 1,000,000 elements (literals, `حد` ranges, append/extend,
  conversions); string/list repetition and integer powers are guarded by
  result-size estimates. Sindhi function calls are capped at 400 frames
  (~2,400 Python frames), and Python's own recursion limit is set to 3,000
  as a backstop for recursion the Sindhi cap cannot see (e.g. deeply
  nested parentheses in the parser). 10,000-frame recursion and 10,000
  nested parentheses both end in a clean Sindhi error, not a crash.
  Program output is capped at 1,000,000 characters.
- **T3 — Plain-text output only.** The worker returns output as text and
  the page renders it with `textContent` into a `<pre>`. The demo's own
  code uses no `innerHTML`, `eval(`, `new Function` or `document.write`.
  The Content-Security-Policy below blocks script injection as a second
  layer.
- **T4 — Sandboxed interop.** Python interop (`ٻاهري ڪم`) runs under AST
  validation, restricted builtins and an import allowlist of exactly
  `math`, `random`, `json` and `datetime`. Blocked: every other import
  (`os`, `sys`, `subprocess`, `importlib`, `js`, `pyodide.*`, `platform`,
  …), dunder attribute access, and dangerous names (`eval`, `exec`,
  `open`, `compile`, `__import__`, `getattr`, …). The file builtins
  (`فائل_پڙهيو` / `فائل_لکيو`) are disabled. The worker never touches
  browser storage or the DOM.
- **T5 — Pinned, self-hosted dependencies.** No CDN and no third-party
  scripts at runtime:
  - Pyodide 0.29.5 (Python 3.13.2), from the official
    `pyodide-core-0.29.5.tar.bz2` release asset (SHA-256
    `ab08aafc11a3c9a0fe73825eb2cec78bda9464348dd17414e7ec0132ef3451e8`),
    hosted in `docs/pyodide/`.
  - Vazirmatn v33.003 font (`Vazirmatn-Regular.woff2`,
    `Vazirmatn-Bold.woff2`), hosted in `docs/fonts/`.
  - The example picker fetches only the four bundled examples, same-origin.
- **T6 — In-memory modules only.** The demo's module loader never touches
  the filesystem: modules load only from an in-memory dict of the bundled
  examples, and names containing `/`, `\`, `..` or absolute paths are
  rejected before lookup.

## Content-Security-Policy (meta tag in `docs/index.html`)

```
default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'
```

`'wasm-unsafe-eval'` is required: Pyodide cannot compile its WebAssembly
without it. It allows WebAssembly compilation only, not JavaScript `eval`.
The page has no inline `<script>` or `<style>`; all page logic lives in
`app.js` and `style.css`.

## Tests

`python test_user_code.py` runs the demo's security checks (step limit,
recursion cap, collection ceiling, HTML output, blocked imports, module
path traversal) against `docs/demo_run.py`.

## Reporting a problem

Found a way around these limits? Please open an issue on this repository.
