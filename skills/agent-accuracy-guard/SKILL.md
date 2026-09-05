---
name: agent-accuracy-guard
description: Preflight guard for Zo/Hermes to prevent repeated failures: unauthorized actions, wrong provider/model assumptions, false completion claims, and ignoring Telegram delivery. Use before agent swarms, provider/model selection, sending files, document generation, or any high-risk action.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---
# Agent Accuracy Guard

Use this before high-risk actions.

## Non-negotiable checks

1. **Authorization**
   - If the user asked for a plan first, stop after the plan.
   - Do not run agent swarm, bulk jobs, paid APIs, email, or external sends without explicit approval.
   - "I guess continue" counts as approval only if the user is clearly telling you to continue the same pending action.

2. **Provider/model verification**
   - Never infer model availability from a local proxy unless the user explicitly said to use that proxy.
   - Alibaba Coding Plan is direct Alibaba Model Studio/Coding Plan, not Command Code, OpenCode, 9router, or any local proxy.
   - Verify against the authoritative source or current configured provider before stating a model is available.

3. **Delivery method**
   - Telegram delivery means use Telegram tools/attachments.
   - Do not invoke Resend/email rules for Telegram delivery.
   - If the user asks for an MD file over Telegram, send the actual `.md` file attachment, not a summary.

4. **Known bad recommendations**
   - Do not recommend Meilisearch on this VPS. It has caused memory leaks / RAM exhaustion / daily crashes.
   - Do not recommend local GPU model services; VPS has no GPU.
   - Do not recommend more OCR stacks unless the user explicitly asks; OCR is already strong enough.
   - **Command Code via Hermes**: Do not claim Kimi/command-code lacks Telegram, VPS access, or Hermes skills. Delivery = Hermes Gateway. VPS shell = CLI proxy :9877. Skills = read `SKILL.md` from disk (no native `skill_view`). Load `command-code-proxy` before stating capabilities.

5. **Verification before claiming done**
   - Before saying a file was sent, verify the tool result includes an attachment success.
   - Before saying a field/file/service was fixed, inspect or test it.
   - If not verified, say exactly what was done and what is unverified.
   - **Notary-log cal host:** Before saying Settings shows tokens, "Create my account", or Cal UI exists, verify **deployed** bundle (`bun run build` + service restart + grep dist or live fetch). Code in repo alone is not proof Joseph sees it.
   - Before running `verify-cal-host.mjs`, warn it **wipes** cal DB users/bookings — Joseph's phone token goes stale.
   - Cal "100% complete": split Plan A MVP (paste-link + webhooks on cal host) vs OAuth vs Worker ship vs real Cal booking on user's phone.

5a. **Verify before claiming ABSENCE (hard-won, recurring failure)**
   - Do NOT say "there is no native import / endpoint / feature / file / capability" based on a shallow first-pass grep or memory of "how these tools usually work." This pattern burned the user badly on 2026-07-25: the assistant twice made confident negative claims ("no native 9router→OmniRoute import exists", "Qwen session cookies are not persisted / can't be extracted") that were both **wrong**, and the user correctly called it lying.
   - Before claiming absence of a feature/endpoint/file/capability in a tool on this VPS (OmniRoute, 9router, qwen-gate, etc.):
     1. Grep the source tree for the symbol/endpoint name (case-insensitive, both camelCase and snake_case).
     2. Check the actual routes/endpoints the running server exposes (`curl localhost:<port>/api/...`, read the route files).
     3. Check the actual on-disk state (SQLite tables, browser profiles, `.env`, config files) — don't answer from memory.
     4. Only THEN say "no, it doesn't exist" — and cite what you checked.
   - If you didn't do steps 1-3, say "I need to verify" and do them. A wrong "no" wastes more time than a verification pass. The user has **zero tolerance** for confident-but-unverified negative claims — repeated instances get treated as lying, not as honest mistakes.

6. **Version / update claims (Joe)**
   - Do not equate "installed ≠ latest release" with "you need to update" for Hermes, mem0, QWEN-gate, or 9router unless Joe asked for upgrades or the install is broken/missing.
   - Hermes at `/usr/local/lib/hermes-agent` may be a custom build on purpose.
   - If Joe says an item does not need updating, answer NO — do not override with GitHub/PyPI tags.
   - If you already gave a wrong yes/no in the same thread, correct it in one direct sentence.

## Command

Run:

```bash
python3 /home/workspace/Skills/agent-accuracy-guard/scripts/preflight.py --task "<task>"
```

It prints a checklist to follow before acting.
