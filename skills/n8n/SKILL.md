---
name: n8n
description: Manage n8n workflows and automations via API. Use when working with n8n workflows, executions, or automation tasks - listing workflows, activating/deactivating, checking execution status, manually triggering workflows, or debugging automation issues.
metadata:
  author: sillyhippy.zo.computer
  compatibility: "Created for Zo Computer"
---

# n8n Workflow Management

Comprehensive workflow automation management for n8n platform with creation, testing, execution monitoring, and performance optimization capabilities.

## Setup

**Required environment variables:**
- `N8N_API_KEY` — Your n8n API key (Settings → API in the n8n UI)
- `N8N_BASE_URL` — Your n8n instance URL

Set via Zo [Settings > Advanced](/?t=settings&s=advanced) as secrets, or per-session:
```bash
export N8N_API_KEY="your-api-key-here"
export N8N_BASE_URL="your-n8n-url-here"
```

**Verify connection:**
```bash
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py list-workflows --pretty
```

## Quick Reference

### Workflow Management

```bash
# List workflows
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py list-workflows --pretty
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py list-workflows --active true --pretty

# Get workflow details
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py get-workflow --id <workflow-id> --pretty

# Create workflow from JSON file
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py create --from-file workflow.json

# Activate/Deactivate
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py activate --id <workflow-id>
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py deactivate --id <workflow-id>
```

### Testing & Validation

```bash
# Validate workflow structure
python3 /home/workspace/Skills/n8n/scripts/n8n_tester.py validate --id <workflow-id>
python3 /home/workspace/Skills/n8n/scripts/n8n_tester.py validate --file workflow.json --pretty

# Dry run with test data
python3 /home/workspace/Skills/n8n/scripts/n8n_tester.py dry-run --id <workflow-id> \
  --data '{"email": "test@example.com"}'
```

### Execution Monitoring

```bash
# List recent executions
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py list-executions --limit 10 --pretty
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py list-executions --id <workflow-id> --limit 20 --pretty

# Manual execution
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py execute --id <workflow-id>
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py execute --id <workflow-id> \
  --data '{"key": "value"}'
```

### Performance Optimization

```bash
python3 /home/workspace/Skills/n8n/scripts/n8n_optimizer.py analyze --id <workflow-id> --pretty
python3 /home/workspace/Skills/n8n/scripts/n8n_optimizer.py suggest --id <workflow-id> --pretty
python3 /home/workspace/Skills/n8n/scripts/n8n_optimizer.py report --id <workflow-id>
python3 /home/workspace/Skills/n8n/scripts/n8n_api.py stats --id <workflow-id> --days 7 --pretty
```

## Script Locations

All scripts live at `/home/workspace/Skills/n8n/scripts/`:
- `n8n_api.py` — Core API client
- `n8n_tester.py` — Testing & validation
- `n8n_optimizer.py` — Performance optimization

## Troubleshooting

**Missing API key:**
```
Error: N8N_API_KEY not found in environment
```
Set the env var or save as a secret in [Settings > Advanced](/?t=settings&s=advanced).

**Connection error (401):**
1. Verify API key is correct
2. Check N8N_BASE_URL
3. Confirm API access enabled in n8n
