# Data Model

## Core Concepts

- `CompositionRequest`: processing options for canvas and shadow
- `CompositionResult`: generated PNG bytes and output dimensions
- `SegmentationProvider`: contract for future background removal adapters

## Important Constraint

At the moment, inputs without an alpha channel are rejected by the composition pipeline because no cutout model is wired yet.
