# Code Style

## Scope

This document holds authoring conventions that are too detailed for `AGENTS.md`.

## Language

- User-facing docs and generated investment reports: Chinese
- Code comments and technical explanations inside code: English
- Financial indicators and market terms: keep standard English abbreviations

## Python

### Imports

- Standard library first, then third-party, then local imports
- No wildcard imports
- Separate import groups with blank lines

### Naming

- Functions and variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`
- Skill directories: `hyphen-case`

### Formatting

- Prefer f-strings
- Soft max line length: 100
- Indentation: 4 spaces
- Leave two blank lines between top-level functions and classes

### Error Handling

- Use explicit `try` / `except`
- Return or raise meaningful error messages
- Avoid bare `except:`

### Comments

- Add docstrings for modules and non-trivial functions
- Use inline comments only for logic that is not obvious from code structure
- Keep comments short and technical

## TypeScript / Frontend

- Follow the existing Next.js + React + Tailwind patterns in `apps/web`
- Preserve the current app structure and naming conventions
- Put browser-facing API access behind the backend layer only
- Avoid introducing direct skill or runtime coupling into the frontend

## Skills

### Required Layout

```text
skill-name/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

### Rules

- `SKILL.md` must include YAML frontmatter with `name` and `description`
- Keep `SKILL.md` concise; move long references into `references/`
- Do not add extra top-level docs like `README.md` unless there is a clear need
- Reuse templates and assets instead of duplicating them

### Output Files

- Write generated artifacts under `output/`
- Create directories with `exist_ok=True`
- If the target filename already exists, append numbered suffixes such as `(1)` and `(2)`

## Documentation

- Keep index files short and link outward
- Put layer-specific detail near the layer it describes
- Put skill-specific detail inside the skill directory
