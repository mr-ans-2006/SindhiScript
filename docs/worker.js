/* SindhiScript browser demo — worker.
 *
 * The interpreter runs ONLY in this worker, never on the UI thread, so a
 * hung program can be killed with worker.terminate() and the page survives.
 * This worker fetches same-origin files only, never touches browser
 * storage, the DOM, or the network beyond this site.
 */
"use strict";

var pyodide = null;
var bootPromise = null;

/* The interpreter files shipped in interpreter/سنڌي/ (demo-patched copies). */
var INTERPRETER_FILES = [
  "__init__.py",
  "tokenizer.py",
  "lexer.py",
  "parser.py",
  "ast_nodes.py",
  "environment.py",
  "errors.py",
  "evaluator.py",
  "stdlib.py",
  "module_loader.py"
];

async function boot() {
  if (bootPromise) {
    return bootPromise;
  }
  bootPromise = (async function () {
    importScripts("pyodide/pyodide.js");
    pyodide = await loadPyodide({ indexURL: "pyodide/" });
    pyodide.runPython("import sys; sys.path.insert(0, '/')");
    var fs = pyodide.FS;
    try {
      fs.mkdir("/interpreter");
    } catch (e) {
      /* already exists */
    }
    try {
      fs.mkdir("/interpreter/سنڌي");
    } catch (e) {
      /* already exists */
    }
    for (var i = 0; i < INTERPRETER_FILES.length; i++) {
      var name = INTERPRETER_FILES[i];
      var response = await fetch("interpreter/سنڌي/" + name);
      if (!response.ok) {
        throw new Error("Could not load interpreter file: " + name);
      }
      fs.writeFile("/interpreter/سنڌي/" + name, await response.text());
    }
    var harness = await fetch("demo_run.py");
    if (!harness.ok) {
      throw new Error("Could not load demo_run.py");
    }
    fs.writeFile("/demo_run.py", await harness.text());
    pyodide.runPython("import demo_run");
  })();
  return bootPromise;
}

self.onmessage = async function (event) {
  var msg = event.data || {};
  if (msg.type === "boot") {
    try {
      await boot();
      self.postMessage({ type: "ready" });
    } catch (err) {
      self.postMessage({
        type: "boot-error",
        error: String((err && err.message) || err)
      });
    }
    return;
  }
  if (msg.type === "run") {
    try {
      await boot();
      pyodide.globals.set("demo_payload_json", msg.payloadJson);
      var resultJson = pyodide.runPython(
        "demo_run.run_demo_json(demo_payload_json)"
      );
      self.postMessage({ type: "result", result: JSON.parse(resultJson) });
    } catch (err) {
      self.postMessage({
        type: "result",
        result: {
          status: "error",
          output: "",
          error: "غلطي: " + String((err && err.message) || err)
        }
      });
    }
  }
};
