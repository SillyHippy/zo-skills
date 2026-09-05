---
name: browser-automation
description: Automate web browser interactions using natural language via CLI commands. Use when the user asks to browse websites, navigate web pages, extract data from websites, take screenshots, fill forms, click buttons, or interact with web applications.
metadata:
  author: sillyhippy.zo.computer
  compatibility: "Created for Zo Computer"
---
# Browser Automation

Automate browser interactions using the `agent-browser` CLI on Zo Computer.

## Available Tool

The `agent-browser` CLI is installed at `/usr/local/bin/agent-browser`. It auto-detects Chrome or falls back to Edge.

## Commands

```bash
agent-browser open <url>                    # Navigate to URL
agent-browser snapshot -i -c                # Accessibility tree with @refs (primary way to read page)
agent-browser snapshot -c                   # Full tree with text content
agent-browser screenshot                    # Viewport screenshot, image returned inline
agent-browser click <@ref>                  # Click element by ref
agent-browser fill <@ref> <text>            # Clear and type into field
agent-browser type <text>                   # Type at cursor
agent-browser press <key>                   # Enter, Tab, Escape, etc.
agent-browser select <@ref> <value>         # Select dropdown value
agent-browser scroll down/up [px]           # Scroll
agent-browser get text <@ref>               # Get text of element
agent-browser eval <js>                     # Execute JavaScript
agent-browser wait --load networkidle       # Wait for page load
agent-browser tab                           # List tabs
agent-browser tab new [url]                 # New tab
```

## Workflow

1. `agent-browser open <url>` — Navigate to page
2. `agent-browser snapshot -i -c` — Read page content with element refs
3. Interact using `@ref` values from snapshot
4. Re-snapshot after changes to verify results

## Login Flow

If the user mentions logging in or signing in:

```bash
agent-browser close
agent-browser --headed open <url>
```

This shows the browser window so the user can enter credentials. Wait for confirmation before continuing.

## Best Practices

1. **Always navigate first** before interacting
2. **Use snapshot to read page content** — don't guess element refs
3. **Use screenshot when user wants to see the page visually**
4. **Be specific** in action descriptions
5. **Close browser** when done: `agent-browser close`
6. **Stop and ask the user** after 2-3 consecutive failures

## Error Recovery

If navigation fails due to anti-bot protection, try alternative approach or ask user.
If element not found after page load, scroll down once then retry.
If buttons can't be clicked due to overlays, use keyboard: `agent-browser press Tab` then `agent-browser press Enter`.

## Zo Browser Tools (Alternative)

Zo also has built-in browser tools that work through the app:

- `open_webpage(url)` — Navigate to URL
- `view_webpage()` — Get current page content as markdown + screenshot
- `use_webpage(task)` — Interact with the current page

Use `agent-browser` for efficiency on unauthenticated sites. Use Zo browser tools for authenticated sessions and when sites block the CLI browser.