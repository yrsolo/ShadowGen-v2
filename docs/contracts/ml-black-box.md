# ML Black Box Contract

At the first stage the old ML core is used as an external black box.

## v2 Position

ShadowGen v2 does not adopt legacy contracts as its own public source of truth. Instead, the worker-side legacy adapter maps v2 requests into whatever the old core currently expects.

## v2 Input Model

- source image bytes
- render request with:
  - source asset reference
  - shadow settings
  - background settings
  - output settings
  - pipeline version

## Adapter Responsibility

- map v2 request to legacy transport payload
- call the legacy service
- parse legacy response
- normalize output into v2 pipeline artifacts

## Design Rule

Legacy compatibility is an adapter concern only. v2 request and response models are optimized for the new architecture, job flow, and future pipeline evolution.

## Current Legacy Shape

Based on the current `ShadowGEN` repository, the legacy `/v1/process` endpoint accepts an image plus form fields like `rot`, `max_objects`, and `return_debug`, and returns JSON with `images`, `meta.timings_ms`, and `warnings`. This is treated as an implementation detail of the adapter, not a public v2 contract.

Sources:

- https://raw.githubusercontent.com/yrsolo/ShadowGEN/master/ML_server.py
- https://raw.githubusercontent.com/yrsolo/ShadowGEN/master/contracts/contracts.py
