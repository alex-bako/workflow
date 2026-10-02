# 0004 — Titles are kept as typed

Status: accepted.

An item's `title` is exactly the text the user typed, minus the URL. Parsing never
rewrites or drops words of the title; features that need tokens from it read them
alongside the title and leave the title intact. Display code may hide tokens.
