# System Overview

## Current State

The repository is backend-first. The current implementation exposes a FastAPI service with a composition pipeline that takes a transparent foreground image, places it on a white background, and generates a soft offset shadow.

## Target Flow

1. Receive a source image
2. Remove or obtain the object mask
3. Normalize object placement on a white canvas
4. Render a soft natural shadow
5. Return the final image and processing metadata

## Main Layers

- `entrypoints`: HTTP routes and request parsing
- `application`: orchestration of image processing use cases
- `domain`: value objects and processing contracts
- `adapters`: external implementations such as segmentation providers
- `config`: centralized runtime settings

## Current Limitation

The repository does not yet include a production background removal model. Only the composition part is implemented in code today.

## Related Docs

- [Backend](backend.md)
- [Data Model](data-model.md)
- [API Reference](../reference/api.md)
