---
name: summarize-pro
description: When user asks to summarize text, articles, documents, meetings, emails, YouTube transcripts, books, PDFs, reports, conversations, or any long content. All processing happens locally — NO external API calls.
metadata:
  author: sillyhippy.zo.computer
  compatibility: "Created for Zo Computer"
---

# Summarize Pro — AI Summarization Engine

All data stored under `/home/workspace/Skills/summarize-pro/data/`:

- `settings.json` — user preferences and stats
- `history.json` — summary history with timestamps
- `saved.json` — saved/bookmarked summaries
- `templates.json` — custom summary templates

## Setup

On first use, create the data directory:
```bash
mkdir -p /home/workspace/Skills/summarize-pro/data
```

## When To Activate

Respond when user says: "summarize", "summary", "tldr", "eli5", "key takeaways", "action items", "bullet points", "executive summary", "compare", "meeting summary", "email summary", "thread summary", "chapter summary", "save summary", "summary history", "summary stats"

## Default Output Format

```
SUMMARY

[3-5 bullet points capturing the main ideas]

Stats: [X] words → [Y] words ([Z]% reduction)
```

## Behavior Rules

1. **Always count words** — show original vs summary word count
2. **Be accurate** — never add information not in the original text
3. **Be concise** — remove fluff, keep substance
4. **Preserve key facts** — names, numbers, dates, quotes must stay accurate
5. **Never fabricate** — if something isn't in the text, don't include it
6. **Auto-log** every summary to history.json
7. **Update stats** after every summary

## Commands

```
SUMMARIZATION:
  "summarize [text]"          — Default summary (auto-detect format)
  "tldr [text]"               — 1-2 sentence summary
  "bullets [text]"            — Bullet point summary
  "eli5 [text]"               — Explain Like I'm 5
  "key takeaways [text]"      — Top insights ranked
  "action items [text]"       — Extract tasks & deadlines
  "exec summary [text]"       — Business executive format
  "summarize in 50 words"     — Custom length
  "meeting summary [text]"    — Meeting notes format
  "email summary [text]"      — Email digest format
  "compare [text A] vs [text B]" — Side-by-side comparison
  "thread summary [text]"     — Conversation summary
  "chapter summary [text]"    — Book/document chapter
  "progressive summary [text]"— All levels (TL;DR → Short → Medium)

MANAGEMENT:
  "save summary"              — Bookmark last summary
  "show saved summaries"      — View bookmarks
  "summary history"           — Past summaries log
  "summary stats"             — Your stats & achievements
```
