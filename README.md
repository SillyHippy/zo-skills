# Zo Skills & MCP Tools Hub

> **Curated, production-tested skills, MCP servers, and automation tools for Zo Computer & Autonomous AI Agents.**

Maintained by **[SillyHippy](https://github.com/SillyHippy)**.

---

## Included MCP Servers & Tools

### 1. `zo-snapshot`
- **What it is:** Instant, differential snapshot & comparison engine for Zo Computer.
- **Key Capabilities:**
  - Hardlink Copy-on-Write (COW) snapshots (< 100ms creation).
  - Word-for-word unified diffs (identical to GitHub PR diffs).
  - Native Zo VM renewal lifecycle hook (`renewal-hooks.d`).
  - Standalone CLI, local REST API (`:3090`), and JSON-RPC 2.0 MCP server.
- **Directory:** [`mcp-servers/zo-snapshot/`](./mcp-servers/zo-snapshot)

### 2. `flat-pdf-fill` (MCP Server)
- **What it is:** Enhanced OCR-assisted PDF form filler with printed-line detection.
- **Key Capabilities:**
  - Optical character recognition with line-trap detection.
  - Form field auto-discovery and typewriter-style value placement.
  - Manual anchor coordinate overrides and review queues.
- **Directory:** [`mcp-servers/flat-pdf-fill/`](./mcp-servers/flat-pdf-fill)

### 3. `zo-playbook`
- **What it is:** The complete Zo Computer power-user hardening & workaround guide.
- **Topics:** Docker sandboxing on gVisor, persistent MCP OAuth, disk snapshot reboots, and cross-model bridges.
- **Documentation:** [`docs/zo-playbook.html`](./docs/zo-playbook.html)

---

## Community credit: `zo-mitigations` by Provisional9448

- **Author:** [Provisional9448](https://github.com/Provisional9448) — repo: [Provisional9448/zo-mitigations](https://github.com/Provisional9448/zo-mitigations)
- **What it is:** stdlib-only toolkit for Zo turn limits, random restarts, and task recovery (turn budget, durable checkpoints, restart monitor, local-inbox handoff, optional ACP completion adapter).
- **Validated here:** 33/33 offline tests pass; budget/monitor/checkpoint/recover/local-inbox verified on Zo 2026-09-12. Live ACP rewiring intentionally not done.
- **Install (their repo, not vendored here):** `git clone https://github.com/Provisional9448/zo-mitigations.git` then follow its `docs/INSTALL_WITH_ZO.md` (preview install first, state dir `700`, monitor as internal service with no public endpoint).

---

## 1-Line Installer for Zo Computer

To install the entire suite onto any Zo Computer / Linux instance:

```bash
curl -sL https://raw.githubusercontent.com/SillyHippy/zo-skills/main/install.sh | bash
```

---

## Fork and pull requests

This repo is public. Anyone with a GitHub account can fork it and open a PR against `main`. They cannot push directly here — you review and merge.

1. Fork: https://github.com/SillyHippy/zo-skills/fork
2. Clone your fork, branch off `main`, push, then Compare & pull request.

Details: [CONTRIBUTING.md](CONTRIBUTING.md)

Issues: https://github.com/SillyHippy/zo-skills/issues

---

## License

[MIT](LICENSE)
