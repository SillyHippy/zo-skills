# Contributing to zo-skills

PRs from forks are welcome. You do not need write access to this repo.

Anyone with a GitHub account can:

1. Fork this repository
2. Push a branch to **their** fork
3. Open a Pull Request against `SillyHippy/zo-skills` branch `main`

They cannot push directly to this repository. That is expected. You review and merge PRs.

## Fork → branch → PR

1. Fork: https://github.com/SillyHippy/zo-skills/fork
2. Clone your fork:

   ```bash
   git clone https://github.com/YOUR_USER/zo-skills.git
   cd zo-skills
   git remote add upstream https://github.com/SillyHippy/zo-skills.git
   ```

3. Create a branch from `main`:

   ```bash
   git checkout main
   git pull upstream main
   git checkout -b your-change
   ```

4. Commit, push to **your fork**, then open a Pull Request:

   ```bash
   git push -u origin your-change
   ```

   Target:

   - base repo: `SillyHippy/zo-skills`
   - base branch: `main`
   - head: `YOUR_USER:your-change`

Direct URL after you push:

`https://github.com/SillyHippy/zo-skills/compare/main...YOUR_USER:your-change`

## What to include

- One change per PR when you can.
- Do not commit secrets, `.env`, credentials, or personal case data.
- Skills belong under `skills/<name>/` with a `SKILL.md`.
- MCP servers belong under `mcp-servers/<name>/`.

## Issues

Bugs and feature requests: https://github.com/SillyHippy/zo-skills/issues
