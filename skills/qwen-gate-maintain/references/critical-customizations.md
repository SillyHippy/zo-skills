# Critical Customizations for qwen-gate

This document explains the non-upstream changes that must be preserved or re-applied after a `git pull` or fresh clone.

## 1. BASE_PATH / Reverse Proxy Support (Dashboard)

**Problem**: When qwen-gate runs behind a reverse proxy (e.g. at `/qwen`), all links and script sources break because they are absolute (`/dashboard/...`).

**Solution**: 
- Read `X-Forwarded-Prefix` header.
- Inject `window.BASE_PATH`.
- Rewrite every `href="/..."` and `src="/..."` in the served HTML.

**Files modified**:
- `src/routes/dashboard/dashboardRoutes.ts`

**Current correct rewrite logic** (single-pass, idempotent):

```ts
if (basePath) {
  const rewrite = (attr: string, url: string) => {
    if (url.startsWith(basePath + '/')) return `${attr}${url}`;
    return `${attr}${basePath}${url}`;
  };
  output = output.replace(/(href="|src=")(\/[^"]*)/g, (_, attr, url) => rewrite(attr, url));
}
```

The patch is stored in `patches/00-basepath-reverse-proxy.patch`.

## 2. Tool Stripping + Context Size Protection (for Qwen free tier)

**Problem**: 
- Hermes sends 100–150+ tool definitions. Qwen's free web API chokes on the huge `local_mcp` payload and returns empty content.
- Large context files (system + tools + history) also cause silent empty replies.

**Solutions** (both required):

A. Set `TOOL_CALLING=false` in config (already the default in our setup). This tells the proxy to omit the huge `local_mcp` object.

B. Code changes in:
   - `src/routes/chatHelpers.ts` — only build `local_mcp` when `_toolCalling === true`.
   - `src/routes/chat.ts` — cap the context file uploaded to Qwen at ~30k chars, prioritize tool results + recent history.

These changes are in `patches/01-tool-stripping-context-cap.patch`.

Without both, you will see "model returned empty content" errors from Hermes when using `qwen3.7-plus` or `qwen3.7-max` through this gateway.

### Important Clarification: TOOL_CALLING=false still supports tool calls

Setting `TOOL_CALLING=false` does **not** disable tool calling.

- It only disables sending the *rich structured schema* (`local_mcp` with full input_schema for every tool) to Qwen.
- The proxy still:
  1. Sends a **textual list** of available tools in the system instructions.
  2. Tells the model: *"To call a tool, respond with the tool call in the appropriate format."*
  3. The model outputs tool calls in Qwen's native XML format (e.g. `<function=tool_name><parameter=arg>value</parameter></function>`).
  4. qwen-gate's `xmlToolParser.ts` + streaming/non-streaming handlers detect these XML blocks, parse them, and convert them back into proper OpenAI-style `tool_calls` objects that Hermes receives.

From Hermes' perspective, tool calling works normally. The `false` setting is a necessary compatibility layer because the free Qwen web endpoint cannot handle large tool schema payloads.

## 3. Custom Instructions & Tool Usage (Safe Merging)

**Warning**: Enabling `USE_CUSTOM_INSTRUCTION=true` causes qwen-gate to **completely replace** the `DEFAULT_SYSTEM_PROMPT` with whatever is in `CUSTOM_INSTRUCTION`.

The default prompt contains critical instructions about:
- Message format (`<user>`, `<assist>`, etc.)
- How to read the `context.txt` file
- Where tool results live (`<tool-results>`)
- Rules for reading previous tool outputs

If you only put tool format instructions in the custom field, you will lose this behavior and tool results may stop working properly.

### Safe way to add tool calling guidance

Use the pre-merged file:

**`/home/workspace/Skills/qwen-gate-maintain/references/safe-custom-instruction.txt`**

This file contains:
- The complete original `DEFAULT_SYSTEM_PROMPT`
- Additional strong guidance for using the exact XML tool call format

**How to apply it safely:**

1. Open the qwen-gate dashboard → **Settings**
2. Copy the entire content from the file above (starting from `# System Prompt — Qwen Gateway Agent` down to the end of the instruction).
3. Paste it into the **CUSTOM_INSTRUCTION** text area.
4. Check the box for **USE_CUSTOM_INSTRUCTION** (set to true).
5. Click **Save Changes**.
6. Restart qwen-gate:
   ```bash
   supervisorctl -c /etc/zo/supervisord-user.conf restart qwen-gate
   ```
7. Verify with the skill's `scripts/verify.sh`.

You can also edit `config.json` directly and restart.

### Optional short version (if you want minimal addition)

If you prefer to keep it very short and are okay with potential overlap, you can try just this addition at the end of the default prompt, but the full merged version above is safer.

## 4. Supervisor Command (must use Bun directly)

Old (fragile): `npx tsx src/cli.ts start --host 0.0.0.0`

Correct:
```bash
command=bash -c 'cd /home/workspace/Projects/qwen-gate && bun src/index.tsx --host 0.0.0.0'
```

See `references/supervisor-block.conf`.

## 5. Important Runtime Settings

See `references/recommended-config.json`. The two most important ones for Hermes compatibility are:

- `TOOL_CALLING`: "false"
- `CLEAN_OUTPUT`: "true"

## Workflow After `git pull` or Fresh Clone

1. `cd /home/workspace/Projects/qwen-gate`
2. `git pull` (or clone)
3. `cp /home/workspace/Skills/qwen-gate-maintain/references/recommended-config.json config.json`
4. Apply patches:
   ```bash
   /home/workspace/Skills/qwen-gate-maintain/scripts/apply-patches.sh
   ```
5. `bun install`
6. `bun run build`
7. Update supervisor (copy the block from references/supervisor-block.conf into `/etc/zo/supervisord-user.conf`)
8. `supervisorctl -c /etc/zo/supervisord-user.conf reread && supervisorctl -c /etc/zo/supervisord-user.conf update`
9. Restart: `supervisorctl -c /etc/zo/supervisord-user.conf restart qwen-gate`
10. Run `scripts/verify.sh`

## Verification Commands

See `scripts/verify.sh`.

## Notes
- The repo's `package.json` still says version 0.7.0 even on post-0.8.0 commits. Do not trust the version string.
- Dashboard static files are served from `src/routes/dashboard/public/`, not `dist/`.
- Always stop via supervisorctl first — the service is stubborn about auto-restarting.
- Tool calling works through XML parsing even when TOOL_CALLING=false. No per-tool custom instructions are required for basic operation.