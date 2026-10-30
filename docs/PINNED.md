# Pinned versions

## Pyodide — 0.29.5 (self-hosted, no CDN)

- Release asset: `pyodide-core-0.29.5.tar.bz2` from
  https://github.com/pyodide/pyodide/releases/download/0.29.5/pyodide-core-0.29.5.tar.bz2
  (the `pyodide-core` asset is the browser dist: `pyodide.js`,
  `pyodide.asm.wasm`, `python_stdlib.zip`. The 408 MB full release
  tarball is NOT needed.)
- SHA-256 of the downloaded tarball:
  `ab08aafc11a3c9a0fe73825eb2cec78bda9464348dd17414e7ec0132ef3451e8`
- Hosted in: `pyodide/` (14 MB extracted).
- Verified: loaded in Node 24 from the self-hosted files;
  `pyodide.version` reported `0.29.5`, embedded Python `3.13.2`.
  Never `latest`, never a guessed version.

## Font — Vazirmatn v33.003 (self-hosted)

- `fonts/Vazirmatn-Regular.woff2` (50,684 bytes) and
  `fonts/Vazirmatn-Bold.woff2` (51,020 bytes), from the project's
  `fonts/webfonts/` directory on jsDelivr (gh rastikerdar/vazirmatn).
  Verified woff2 magic bytes (`wOF2`). No font CDN at runtime.

## Interpreter — SindhiScript master at build time

- Source: read-only clone of https://github.com/mr-ans-2006/SindhiScript
  in `source/` (study only, NOT shipped). Demo copies with security
  patches live in `interpreter/سنڌي/`; regenerate with
  `patches/rebuild_demo.py` (see PATCHES.md).
