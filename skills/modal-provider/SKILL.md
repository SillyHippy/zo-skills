---
name: modal-provider
description: Manage Modal credentials, check status, deploy and interact with Modal-hosted AI models (including GLM-5.1). Use when the user mentions Modal, GLM-5, GLM-5.1, or needs to work with the Modal cloud platform.
compatibility: Created for Zo Computer
metadata:
  author: sillyhippy.zo.computer
---

# Modal Provider

## Overview

Modal is a serverless cloud platform. The user has two sets of credentials configured.
Modal CLI tokens are for deploying/running code on Modal.
The GLM-5.1 endpoint is a separate OpenAI-compatible API.

## Modal CLI Tokens

Token 1 (default profile):
- Token ID: ak-uIGIJqpssEEXbL5Mm2seHL
- Token Secret: as-e8kFg2N4VqJHJcaE0muNrr

Token 2 (backup):
- Token ID: ak-bSUpj1kB0F6OhENx3KM23x
- Token Secret: as-BgWQBZRgQpa50pr5rF7opY

## GLM-5.1 Endpoint (OpenAI-compatible)

- Base URL: `https://api.us-west-2.modal.direct/v1`
- Model name: `zai-org/GLM-5.1-FP8`
- Endpoint token: Generated separately at https://modal.com/glm-5-endpoint
- Auth: Bearer token in Authorization header

## Connecting to Zo Computer as BYOK Provider

1. Go to [Settings > AI > Providers](/?t=settings&s=ai&d=providers)
2. Click "Add provider"
3. Select "Custom OpenAI-compatible provider"
4. Set:
   - Name: `Modal GLM-5.1`
   - Base URL: `https://api.us-west-2.modal.direct/v1`
   - API Key: (the endpoint token from modal.com/glm-5-endpoint)
5. Save, then go to [Settings > AI > Models](/?t=settings&s=ai&d=models) and set it as default or per-channel model

## Commands

- `modal token set --token-id <id> --token-secret <secret>` — switch tokens
- `modal config show` — show current config
- `modal dashboard` — open Modal dashboard
- `modal run <script.py>` — run a Python script on Modal
- `modal deploy <app.py>` — deploy a Modal app
- `hermes gateway status` / `hermes gateway run` — Hermes gateway (also uses Modal backend)

## Scripts

- `scripts/modal-status.sh` — Check Modal token status
- `scripts/modal-test.py` — Test GLM-5.1 endpoint connectivity
