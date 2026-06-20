# Current Task

## Task

Diagnose why the reachable new ML service at `http://192.168.1.8:9001` is not producing processed images through the worker, and make worker/API diagnostics expose the failure point clearly.

## Goal

Make failures visible at the exact boundary where they happen: ML handshake, request submission, async polling, result mapping, artifact storage, or queue/job lifecycle.

## Scope Of This Stage

- verify the live ML service handshake shape when reachable from this environment
- inspect worker trace and diagnostics surfaces for swallowed ML errors
- add concise ML submit/poll diagnostic context to failed jobs and worker state
- keep API free of direct private ML calls
- update tests, docs, and evidence

## Risks

- diagnostics must not store base64 image payloads or large ML responses
- private worker/ML hosts must stay behind the worker-side control plane
