# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.

## Artifacts

### Veritas — Developer Knowledge Interface (`artifacts/veritas`)
- React + Vite frontend at `/` (root path)
- Ask state (question input + example questions) → Reading state (document UI with source map)
- Calls `POST /api/veritas/synthesize` with a developer question
- Renders AI-generated answer as a structured document (concepts, inline citations, source sidebar)
- Citation hover → source panel detail; scroll position → sidebar active concept tracking

### API Server (`artifacts/api-server`)
- Express 5 backend, built with esbuild
- **`/api/veritas/synthesize`** (POST): Claude synthesis endpoint — takes a question, returns `VeritasAnswer` JSON with `ideas[]` and `sources{}`
- **`/api/veritas/examples`** (GET): Hardcoded example developer questions for the landing UI
- Uses `@workspace/integrations-anthropic-ai` (Replit AI Integrations proxy — no API key needed)
- Model: `claude-sonnet-4-6`

### Mockup Sandbox (`artifacts/mockup-sandbox`)
- Canvas design mockup for Veritas at `/__mockup/preview/veritas/App`
- Iterative UI prototype — reference only

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.
