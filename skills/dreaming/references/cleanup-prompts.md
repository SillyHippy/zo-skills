# Cleanup Interaction Prompts

Use these literal prompt templates when running the `dreaming` skill in deep mode. Adjust wording for tone, but preserve the structure.

## Per Stale Folder

> Folder: ``
> Last touched: `` (`` days ago)
> Contents: `` files, `` total
> Best guess at purpose: ``
>
> Choose:
> 1. **Archive** → move to `Archive///` and add a one-line note in the heartbeat report
> 2. **Delete** → `rm -rf ` (requires you to type the literal folder name to confirm)
> 3. **Keep** → record "still needed as of " so the next heartbeat won't surface it
> 4. **Defer** → leave it, surface again next run
>
> Reply with 1, 2, 3, or 4.

## Per Context-Bleed File

> File: ``
> Suspected correct location: ``
> Why I think it's misplaced: ``
>
> Choose:
> 1. **Move** → relocate to suggested path
> 2. **Keep here** → record an exception so I stop flagging it
> 3. **Different location** → tell me where
> 4. **Defer** → surface again next run

## Per Skill Candidate

> Workflow detected: ``
> Occurrences in last 30 days: `` (``)
> Proposed scope: ``
>
> Proposed `SKILL.md` skeleton:
> ```
> ---
> name: 
> description: 
> ---
> # 
> ## When to use
> ## Steps
> ## Output
> ```
>
> Choose:
> 1. **Scaffold it** → create the SKILL.md and open for me to flesh out
> 2. **Defer** → keep watching, surface again if it happens a 4th time
> 3. **Reject** → mark as "not a skill, just a coincidence" so I stop suggesting it

## Per Idle Automation

> `` last fired: `` (`` days ago)
> Last status: ``
> Runs: ``
>
> Choose:
> 1. **Pause** → disable but keep the config
> 2. **Delete** → remove entirely
> 3. **Fix** → leave running, but tell me what to look at
> 4. **Defer** → leave it, surface again next run

## Per Stale Persona

> `` last activated: `` (`` days ago)
> Purpose: ``
>
> Choose:
> 1. **Retire** → remove the Persona
> 2. **Keep** → record "still needed as of "
> 3. **Defer** → surface again next run

## Per Stale Rule

> Rule: ``
> Added: `` (`` days ago)
> Conflict: ``
>
> Choose:
> 1. **Remove** → rule no longer applies
> 2. **Keep** → still relevant
> 3. **Edit** → tell me how to adjust the wording
> 4. **Defer** → surface again next run

## Per Hosted Site / Service

> `` last updated: `` (`` days ago)
> Reachable: ``
> Purpose: ``
>
> Choose:
> 1. **Keep** → still in use
> 2. **Sleep** → take down the public surface but keep the files
> 3. **Retire** → remove the hosted service entirely (after typed confirmation)
> 4. **Defer** → surface again next run

## Confirmation Discipline

For any **Delete** choice, require the user to type the literal item name back. Examples:

> To confirm deleting `Active Projects/Old Campaign/`, type: `Active Projects/Old Campaign/`

This prevents fast-yes mistakes. The friction is the feature.