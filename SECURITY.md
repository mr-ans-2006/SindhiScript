# SindhiScript Browser Demo — Security Notes

This file records the threat model for the public demo (spec Step 0) and
how each threat is defended. At ship time, copy this file to the repo as
`SECURITY.md` (it is kept here for now because this build is local-only).

## Threat model

- **T1 — Hang:** a visitor writes an infinite loop and freezes their own tab.
- **T2 — Memory blowup:** unbounded list/dict construction, deep recursion,
  giant powers or string/list repetition crash the tab.
- **T3 — Output injection (XSS):** program output contains `<script>` or
  HTML and the page renders it as HTML.
- **T4 — Pyodide surface creep:** the import / Python-interop block reaches
  browser APIs (`js`, `pyodide.http`, `localStorage`, `document`).
- **T5 — Supply chain:** Pyodide CDN compromised or version drift;
  bundled `.سن` examples tampered.
- **T6 — Module loader path traversal:** a `.سن` import reads arbitrary
  files from Pyodide's filesystem.

## Defenses (each maps to a threat above)

- **T1 — Worker + two limits.** The interpreter runs in `worker.js`, never
  on the UI thread. A step budget (300,000 steps, counted in the
  evaluator's `execute`/`evaluate` dispatch) raises a graceful Sindhi
  "step limit exceeded" error; the UI thread's 5-second `setTimeout` →
  `worker.terminate()` is the hard backstop, and Reset spins up a fresh
  worker. Measured: an infinite loop errors in ~0.3 s (CPython) /
  ~0.6 s (Pyodide), well under 5 s.
- **T2 — Collection ceilings + recursion caps.** Lists/dicts are refused
  above 1,000,000 elements (literals, `حد` ranges, append/extend,
  conversions); string/list repetition and integer powers are guarded by
  result-size estimates. Sindhi function calls are capped at 400 frames
  (~2,400 Python frames); Python's own recursion limit is set to 3,000
  frames as a backstop for recursion the Sindhi cap cannot see (e.g.
  deeply nested parentheses in the parser). Both caps were measured in
  Node+Pyodide: 10,000-frame recursion and 10,000 nested parens now end
  in a clean Sindhi recursion error, not a wasm stack crash.
- **T3 — Plain-text output only.** The worker returns output as text;
  the UI renders it with `textContent` into a `<pre>` element. No
  `innerHTML`, `eval(`, `new Function`, or `document.write` anywhere in
  the demo's own code (verified by grep). The page CSP (below) blocks
  script injection as a second layer.
- **T4 — Sandboxed interop.** Python interop (`ٻاهري ڪم`) runs under AST
  validation plus restricted builtins plus an import allowlist of exactly
  `math`, `random`, `json`, `datetime`. Blocked: arbitrary imports
  (`os`, `sys`, `subprocess`, `importlib`, `js`, `pyodide.*`, `platform`,
  …), dunder attribute access, and dangerous names (`eval`, `exec`,
  `open`, `compile`, `__import__`, `getattr`, …). File builtins
  (`فائل_پڙهيو` / `فائل_لکيو`) are disabled in the demo. The worker never
  touches browser storage or the DOM.
- **T5 — Pinned, self-hosted Pyodide.** Version 0.29.5, downloaded from
  the official GitHub release and hosted in `pyodide/` (see PINNED.md).
  No CDN, no `latest`, no third-party scripts on the page. The example
  picker fetches only the four hardcoded bundled examples, same-origin.
- **T6 — In-memory modules only.** The demo module loader
  (`patches/module_loader.demo.py`) never touches the filesystem: modules
  load only from an in-memory dict of bundled examples, and names
  containing `/`, `\`, `..`, or absolute paths are rejected before
  lookup. The original loader's `os.path.exists` / `os.listdir` / `open`
  path is gone from the demo copy.

## Content-Security-Policy (meta tag in index.html)

```
default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'
```

**Deviation from the spec, documented here:** the spec's policy had
`script-src 'self'`, but Pyodide cannot compile its WebAssembly without
`'wasm-unsafe-eval'`. This is a narrow, documented exception: it allows
WebAssembly compilation only, not JavaScript `eval`. Without it the demo
cannot run at all. Note the page therefore has no inline `<script>` and
no inline `<style>` — all page logic lives in `app.js` / `style.css`,
because the CSP blocks inline code.

## Extra hardening (beyond the spec)

- Demo output is capped at 1,000,000 characters (truncated with a note).
- The original `time` module was dropped from the interop globals to
  match the spec's exact allowlist (`math`, `random`, `json`, `datetime`).
  The repo's own `سنسار.سن` example therefore stops at its FFI section
  (`import platform` is refused) with a clear message; sections 1–5 run.
  This is labeled in the example picker.
- The recursion cap is 400 (not the spec's ~500) and the Python limit is
  3,000 (not unbounded): measured wasm-stack safety margins (see above).

## Known limits / what still needs a live browser check

- The 5-second `worker.terminate()` backstop, the Reset button, the CSP
  meta tag enforcement, and `importScripts` + `fetch` inside a real web
  worker were verified in Node (same Pyodide, same files) but NOT in a
  real browser yet. Those are browser-only behaviors and must be checked
  in a browser before ship.
- `performance.memory` monitoring (spec 2b, best-effort) was NOT
  implemented: it is Chrome-only and non-portable; the deterministic
  ceilings above are the primary defense.
- The spec's CI checks (grep for `innerHTML`/`eval(`/`new Function`/
  `document.write`, `npm audit` / `pip-audit`) belong in the repo's
  pipeline at ship time and are not part of this local build.

## Ship set (copy only these to the repo at ship time)

`index.html`, `app.js`, `worker.js`, `style.css`, `demo_run.py`,
`pyodide/`, `interpreter/`, `examples/`, `fonts/`, `SECURITY.md`,
`PINNED.md`. Do NOT ship `source/` (the unpatched originals, study
only) or `patches/` (build tooling). At ship time, also decide Pages
auto-publish vs manual with Ali first (lifecycle rule).
