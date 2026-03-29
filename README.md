# ShadowGen v2

ShadowGen v2 is a Python service for preparing clean product images from photos. The target workflow is simple: photograph an item, cut it out from the background, place it on a white canvas, and add a soft natural shadow.

## What It Is

This repository contains the backend-first foundation for an image processing project. At the current stage, the API and pipeline support composition of an already cut out object with a white background and soft shadow, and the repository is structured for the next step: automatic background removal from source photos.

## Why It Exists

The project is aimed at marketplaces, catalog teams, and internal content pipelines that need consistent product images without manually editing every shot. The goal is to make the transformation reproducible, scriptable, and easy to evolve.

## Core Capabilities

- Structured repository with docs, tracking, and agent workflow
- FastAPI backend scaffold for image processing tasks
- Working composition pipeline for transparent PNG input
- Clear extension point for future background removal models

## Quick Start

See:

- [Getting Started](docs/overview/getting-started.md)
- [Repository Map](docs/overview/repository-map.md)
- [Architecture Overview](docs/architecture/system-overview.md)

## Repository Structure

- `apps/` - application code
- `packages/` - shared schemas and reusable contracts
- `docs/` - permanent documentation
- `work/` - active task tracking
- `agent/` - agent operating rules and policies
- `.codex/skills/` - procedural repo skills

## Documentation

Documentation map: [docs/README.md](docs/README.md)

## Agent Workflow

See:

- [AGENTS.md](AGENTS.md)
- [agent/OPERATING_CONTRACT.md](agent/OPERATING_CONTRACT.md)

## Status

Repository foundation is prepared. The current implementation covers API scaffolding and composition of transparent cutouts; automatic background removal from non-transparent photos is the next major step.
