# Web App

Path:

- `apps/web/src`

Entry point:

- `apps/web/src/app/page.tsx`

Responsibilities:

- user upload flow
- render parameter controls
- job polling and result preview
- engineering diagnostics view
- remote worker action requests through the API

Main areas:

- `app/` - route entrypoints and global styles
- `components/` - UI widgets
- `lib/api-client.ts` - API calls
- `lib/types.ts` - frontend API types

Not responsible for:

- direct worker access
- direct ML calls
- shared-state reads outside the API
