# Web App

Path:

- `apps/web/src`

Entry point:

- `apps/web/src/app/page.tsx`

Responsibilities:

- user upload flow
- compact mobile-first render flow with model selection
- larger desktop-oriented render flow for the same product API
- job polling and result preview
- engineering diagnostics view
- remote worker action requests through the API

Main areas:

- `app/` - route entrypoints and global styles
- `components/` - UI widgets
- `lib/api-client.ts` - API calls
- `lib/types.ts` - frontend API types

Current interaction notes:

- the shell now switches between `Min`, `Max`, and `Engineering` modes instead of a separate user-vs-engineering tab split
- the top selector presents the two shadow models as `Top` (`v1-gan`) and `Side` (`v2-diff`)
- `Min` follows the compact preview-first mobile composition from `design/ref`
- the source preview block itself acts as the entry point for upload and device-camera capture
- upload preparation downsizes oversized images and repacks large opaque PNG files as JPEG while preserving transparent PNG files as PNG
- the source preview shows a small clear button after an image is loaded so the operator can quickly replace it
- `Max` keeps the larger desktop-oriented workspace and the previous manual controls
- `Engineering` keeps the current diagnostics and remote worker-control view
- mutating Engineering actions require the operator to enter the API admin token; the token is not baked into the public web build
- lost-job cleanup actions show inline per-job status and API errors, including missing or invalid admin token responses
- after a successful lost-job `Mark failed` or `Delete metadata` action, the card is hidden immediately while diagnostics refreshes from shared state
- Engineering includes a `Clear request cache` admin action that resets duplicate-request cache metadata without deleting jobs or artifacts

Not responsible for:

- direct worker access
- direct ML calls
- shared-state reads outside the API
