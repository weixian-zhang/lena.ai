---
description: Summarize changes and list changed files for a PR message
argument-hint: "[base-branch]"
---
Produce a pull request message from the changes on the current branch compared to `${1:-main}`.

First gather the diff context by running:
- `git diff --stat ${1:-main}...HEAD` (list of changed files)
- `git diff ${1:-main}...HEAD` (full diff to understand what changed)
- `git log --oneline ${1:-main}..HEAD` (commit messages for extra context)

Then output a PR message in exactly this format:

## Summary
A short, plain-language summary (3-6 bullet points) of WHAT changed and WHY, written for a reviewer. Avoid restating every line of the diff — focus on intent and user-facing impact.

## Why
A single one-line sentence explaining why this change was made.

## Changed Files
A bullet list of changed files, each with a brief note of what changed in it. Group related files together if helpful.

Keep it concise and skip any file that only has trivial/whitespace changes. Do not include the raw diff in the output.

Keep the writing simple and plain. Do not worry about grammar, punctuation, or polish — prioritize clarity and brevity over correctness.
