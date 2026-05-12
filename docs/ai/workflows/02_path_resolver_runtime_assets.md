# Workflow 02 — Path resolver and runtime assets

## Scope
Implement a canonical path resolver that separates upstream cache from working data, resolves user lists and fake assets from correct locations, and never generates empty fake `.bin` files.

## Tasks

### 2.1 Canonical path resolver
- Implement or enforce `AppPaths` from `core/paths.py` as the single source of truth for all paths.
- The resolver must understand:
  - portable root;
  - DedZapretData root;
  - runtime files vs user data;
  - upstream cache vs working data.

### 2.2 User list resolution
- Ensure user list files resolve from `DedZapretData/data/lists/`:
  - `list-general-user.txt`
  - `list-exclude-user.txt`
  - `ipset-exclude-user.txt`
- These must NOT live under upstream cache paths like `data/upstreams/flowseal/lists/`.

### 2.3 Fake asset resolution
- Resolve fake assets from runtime zapret fake directory.
- Controlled repair from Flowseal upstream cache (copy, do not modify upstream).
- Never generate empty fake `.bin` files.

### 2.4 Empty file policy
- Accept empty user list files as valid.
- Reject empty fake `.bin` files.

### 2.5 Preflight path checks
- Preflight must check file paths correctly:
  - Values containing `.bin/.txt/.dat/.pem/.crt` should be checked as files.
  - Values with slash/backslash should be checked as files.
  - Hex/modifier values like `0x0F0F0F0F`, `rnd,dupsid,sni=...`, `none` must NOT be checked as files.

## Acceptance criteria
- [ ] Path resolver is the single source of path definitions.
- [ ] User lists resolve from `data/lists/`, not upstream cache.
- [ ] Fake assets resolve from runtime fake dir.
- [ ] No empty fake `.bin` files are created.
- [ ] Empty user list files are accepted without warning.
- [ ] Preflight does not flag hex/modifier values as missing files.