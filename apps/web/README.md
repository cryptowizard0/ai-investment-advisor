# Investment Platform Web

Frontend layer for the three-layer investment agent product.

## Responsibilities

- Owns UI, routing, report reading, and user interaction
- Talks only to the backend layer
- Does not access `.agents/skills` or call `opencode` directly

## Run

```bash
pnpm install
pnpm --dir apps/web dev
```
