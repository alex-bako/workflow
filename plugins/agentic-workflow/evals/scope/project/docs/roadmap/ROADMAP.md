# Reading list roadmap

### Next up

- S1.2

### Stage 1

#### S1.1 — Add and list items

Done.

#### S1.2 — Tags on items

Depends on: S1.1.

1. `T1` — Parse `#tags` from an item line into `tags`.
2. `T2` — Filter the list by one tag.
3. `T3` — Show per-tag counts in the summary line.

Acceptance:
- T1: `parseItem` returns `tags`: the `#word` tokens of the line, lowercased, without `#`, in first-seen order, without duplicates.
- T1: tag tokens are removed from the title; a line without tags yields `tags: []`.
- T2: `filterByTag(items, tag)` in `src/filter.mjs` returns the items carrying the tag, case-insensitively.
- T3: `summary(items)` appends `; tags: a×2, b×1`, sorted by count, then name.

Decided (owner): a tag is a whole whitespace-delimited token, `#` followed by ASCII letters, digits or `_` (`#café` is no tag). Any other token, such as `#work,`, `#work.` or `C#`, is no tag and stays in the title.
