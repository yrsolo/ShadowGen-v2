# API Reference

## Endpoints

### `GET /health`

Returns service status and app name.

### `POST /v1/compose`

Accepts an uploaded image and returns a PNG with a white background and soft shadow.

## Current Input Contract

The uploaded image must already contain transparency. If the input has no alpha channel, the API returns an error because background removal is not implemented yet.
