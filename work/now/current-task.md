# Current Task

## Task

Allow the local worker web interface to change the effective ML service address.

## Goal

Let an operator update the worker runtime ML URL from `http://localhost:8081` without editing Object Storage or using the cloud Engineering page.

## Scope Of This Stage

- add a token-protected local runtime-config update endpoint
- add an ML URL input and save action to the worker dashboard
- publish the changed effective URL into worker runtime state immediately
- update tests, docs, and evidence

## Risks

- changing the URL affects subsequent jobs and capability probing
- the endpoint must require the worker control token
