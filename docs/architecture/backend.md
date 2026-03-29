# Backend Architecture

## Stack

- FastAPI for HTTP transport
- Pillow for image composition
- Pytest for tests

## Request Flow

1. HTTP route validates input
2. Application service builds a composition request
3. Pipeline prepares canvas and shadow
4. Result is returned as PNG bytes

## Near-Term Evolution

- add segmentation adapter for non-transparent inputs
- persist generated artifacts
- expose batch processing mode
