/* SindhiScript browser demo — UI thread.
 *
 * This thread never runs user code. It only sends source text to worker.js
 * and renders the worker's plain-text reply. Output is set with textContent
 * only, so program output can never become HTML.
 */
"use strict";

var worker = null;
var workerDead = false;
var readyResolve = null;
var readyPromise = null;
var runTimer = null;
var exampleSources = {};

/* Only these files may ever be fetched. The picker value is never used as
 * a path directly — it must match one of these entries. */
var EXAMPLES = [
  { file: "سلام.سن", label: "سلام — hello" },
  { file: "سنسار.سن", label: "سنسار — full tour" },
  { file: "لوپ.سن", label: "لوپ — loops and functions" },
  { file: "رياضي.سن", label: "رياضي — math interop (allowed)" }
];

function $(id) {
  return document.getElementById(id);
}

function setStatus(text) {
  $("status").textContent = text;
}

function showResult(result) {
  var text = result.output || "";
  if (result.error) {
    if (text) {
      text += "\n";
    }
    text += result.error;
  }
  $("output").textContent = text;
  switch (result.status) {
    case "ok":
      setStatus("Done.");
      break;
    case "step-limit":
      setStatus("Step limit exceeded — the program ran too long.");
      break;
    case "memory-limit":
      setStatus("Memory limit exceeded.");
      break;
    case "recursion-limit":
      setStatus("Recursion limit exceeded.");
      break;
    case "module-blocked":
      setStatus("Module blocked in demo.");
      break;
    case "interop-blocked":
      setStatus("Python interop blocked in demo.");
      break;
    case "blocked":
      setStatus("Blocked in demo.");
      break;
    case "input-exhausted":
      setStatus("Out of input lines — add lines to the input box.");
      break;
    case "exited":
      setStatus("Program exited.");
      break;
    default:
      setStatus("Error: see output.");
      break;
  }
}

function handleMessage(event) {
  var msg = event.data || {};
  if (msg.type === "ready") {
    setStatus("Ready.");
    if (readyResolve) {
      readyResolve(true);
      readyResolve = null;
    }
  } else if (msg.type === "boot-error") {
    setStatus("Failed to load interpreter: " + msg.error);
    if (readyResolve) {
      readyResolve(false);
      readyResolve = null;
    }
  } else if (msg.type === "result") {
    if (runTimer) {
      clearTimeout(runTimer);
      runTimer = null;
    }
    $("runBtn").disabled = false;
    showResult(msg.result);
  }
}

function startWorker() {
  if (worker) {
    try {
      worker.terminate();
    } catch (e) {
      /* already gone */
    }
  }
  workerDead = false;
  worker = new Worker("worker.js");
  worker.onmessage = handleMessage;
  readyPromise = new Promise(function (resolve) {
    readyResolve = resolve;
  });
  setStatus("Booting interpreter…");
  worker.postMessage({ type: "boot" });
}

async function run() {
  if (workerDead) {
    startWorker();
  }
  var ready = await readyPromise;
  if (!ready) {
    return;
  }
  var stdinText = $("stdin").value;
  var stdinLines = stdinText === "" ? [] : stdinText.split("\n");
  var payload = JSON.stringify({
    source: $("editor").value,
    stdin: stdinLines,
    modules: exampleSources
  });
  $("runBtn").disabled = true;
  setStatus("Running…");
  worker.postMessage({ type: "run", payloadJson: payload });
  if (runTimer) {
    clearTimeout(runTimer);
  }
  runTimer = setTimeout(function () {
    /* Hard backstop: the worker is killed, the page survives. */
    try {
      worker.terminate();
    } catch (e) {
      /* already gone */
    }
    workerDead = true;
    runTimer = null;
    $("runBtn").disabled = false;
    setStatus("Timed out after 5s");
    var current = $("output").textContent || "";
    $("output").textContent = current + "\n[Timed out after 5 seconds — press Reset to try again.]";
  }, 5000);
}

function reset() {
  if (runTimer) {
    clearTimeout(runTimer);
    runTimer = null;
  }
  $("output").textContent = "";
  $("runBtn").disabled = false;
  startWorker();
}

async function loadExamples() {
  var picker = $("example");
  for (var i = 0; i < EXAMPLES.length; i++) {
    var entry = EXAMPLES[i];
    var option = document.createElement("option");
    option.value = entry.file;
    option.textContent = entry.label;
    picker.appendChild(option);
    try {
      var response = await fetch("examples/" + entry.file);
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      exampleSources[entry.file.replace(/\.سن$/, "")] = await response.text();
    } catch (e) {
      option.disabled = true;
    }
  }
  picker.addEventListener("change", async function () {
    var file = picker.value;
    try {
      var response = await fetch("examples/" + file);
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      $("editor").value = await response.text();
    } catch (e) {
      setStatus("Could not load example.");
    }
  });
}

document.addEventListener("DOMContentLoaded", function () {
  $("runBtn").addEventListener("click", run);
  $("resetBtn").addEventListener("click", reset);
  loadExamples();
  startWorker();
});
