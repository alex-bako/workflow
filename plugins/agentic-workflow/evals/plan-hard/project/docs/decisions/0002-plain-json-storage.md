# 0002 — Saved lists are plain JSON

Status: accepted.

Lists are saved as one JSON document with a version number; no database, no
dependencies. Migrations are pure functions in `src/migrations.mjs`.
