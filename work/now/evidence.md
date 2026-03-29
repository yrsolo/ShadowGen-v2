# Evidence

## What Was Checked

- repository structure created from the starter guidance
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
- `python -m pytest`

## What Is Confirmed By Code

- FastAPI app exposes `GET /health`
- composition pipeline generates a white-background PNG with a soft shadow
- non-transparent input is rejected with an explicit error until segmentation is implemented

## What Is Still Assumed

- segmentation model choice
- storage strategy

## What Was Updated

- repository structure
- backend scaffold
- documentation
- tracking
- tests

## Remaining Risks

- non-transparent source photos are not yet supported end-to-end
