---
name: time-awareness
description: |
  Ensure the agent always retrieves the current date/time before constructing
  relative-time queries to prevent wrong-year bugs. Used for any query that
  refers to "today", "now", "this week", "current" events, or time-relative language.
---

## Time Awareness

**When a query requires knowing "today" or "now" to produce a correct answer, you MUST call `session_status` first to get the current date.** This applies to ALL relative time and current-events queries.

### Mandatory Two-Step Process

1. Call `session_status` **ALONE** — never batch it with search or other tools.
2. **WAIT** for the result. Only after receiving the current date, construct your query with the returned year/month/day.

Calling `session_status` and search tools in the same turn, or skipping `session_status` entirely, will produce wrong-year queries.
