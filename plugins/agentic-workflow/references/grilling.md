# Grilling: the planning interview

Every aw planning conversation (`aw-feature`, `aw-discover`, `aw-domain`,
`aw-roadmap`, interactive `aw-plan` and `aw-plan ahead`) interviews this way.
Adapted from the `grilling` skill in mattpocock/skills (MIT).

## Design tree and frontier

Map the subject as a design tree: each decision branches into the decisions that
hang off it. The **frontier** is every open decision whose prerequisites are
settled, the questions that can be asked now without guessing an answer not yet
heard. Work in rounds: ask the frontier, wait, record the answers, recompute it.
A question that depends on another one still open in the same round waits for a
later round. The tree is judgment, not a computed graph; when two answers turn out
to interact, reopen that branch in the next round.

## Asking a round

- One question is one decision. Give two to four real options, recommend one and
  state its tradeoff.
- Claude Code: the interview tool (`AskUserQuestion`), up to four frontier
  questions per prompt, recommended option first; a larger frontier takes
  consecutive prompts in the same round. Codex, or a host without such a tool: the
  round as numbered text the user answers by number:

  ```text
  ❓ Q1 — <title>: <question and options>
  ➡️ <recommended answer>
  ---
  ❓ Q2 — ...
  ```

- Close the round with the count: `N open · M waiting on this round`.
- Asynchronous (a blocked tracker comment): the same numbered text, one round per
  comment, under a two-line brief: what was produced, why it waits, the plan link.
  Name cards and bullets by ID and title, never by a bare issue number.

## Facts are yours, decisions are the user's

Never ask the user what code, docs, project instructions or tools can answer. Look
it up before the round; for a broader search dispatch a scout in the same turn and
hold back only the questions downstream of it. Never answer a decision on the
user's behalf. Inside the delivery loop only an authority line, a settled
`Decisions:` item, an accepted decision record, an accepted plan or code at
`file:line` settles a material decision (behavior a user, a contract or the data
would notice); anything else about it stays open. A non-material choice is the
coordinator's call, recorded with its reason.

## Moves

- A term that conflicts with the domain document: say so at once. A fuzzy or
  overloaded word: propose one canonical term.
- Invent a concrete edge case that forces a boundary: two concepts, a failure, a
  permission, a recovery.
- When the user states how something works, check the code and raise a
  contradiction as a question.
- A question talk cannot settle (look and feel, a flow, how an API reads) leaves
  the interview for a throwaway prototype or a spike with exit evidence and comes
  back as a one-line answer.
- Proportion: a small feature gets a short interview. Do not grill code-level
  detail of distant milestones. Round after round of new branches means the scope
  is too big: split it and grill the pieces. There is no question cap; the user
  steers with "wrap up" or by accepting the plan as it stands.

## Recording

Write each answer into the draft documents as it settles. Keep `Open decisions`
in the Progress section, or in a card's authority section for `aw-plan ahead`:
ID, question, what it waits on, recommendation. A settled one moves to
`Decisions` with its source: user and date, authority line, decision record or
`file:line`. A paused interview resumes on this list's frontier.

Offer a **decision record** when a decision is hard to reverse, surprising without
its context and the result of a real tradeoff. Explicit noes count: a rejected
alternative that will otherwise be proposed again. Use the project's location (its
instructions, else `docs/adr/NNNN-slug.md` with the next free number): a title and
one to three sentences of context, decision and reason. Records are written only
with the user present; a loop coordinator proposes one in its report instead. The
domain document keeps terms and rules, not decision logs.

## Done

The frontier is empty: no material decision is open, and each non-material one is
recorded as a labeled assumption with its recommendation or deferred by the user.
The user then confirms the shared understanding; only then are the documents
accepted. A grilling alone authorizes no code, tracker write or publication.
