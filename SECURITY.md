# Security Notes

This repository should contain **only sanitized configuration**.

## Never commit

- TDX Client ID
- TDX Client Secret
- TDX OAuth access tokens
- Home Assistant long-lived access tokens
- ESPHome Native API encryption keys
- actual Wi-Fi passwords
- ESPHome fallback hotspot passwords
- private TLS keys / certificates
- unrelated personal configuration

## Home Assistant secret

The project expects a private Home Assistant `secrets.yaml` entry:

```yaml
tdx_auth_payload: 'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET'
```

The repository configuration references it with:

```yaml
payload: !secret tdx_auth_payload
```

## ESPHome secrets

The public repository contains only `esphome/secrets.example.yaml`.

Real values belong in the normal private ESPHome secrets mechanism.

## Rotation rule

If a credential has ever appeared in a chat, screenshot, issue, gist, log excerpt, or commit, rotate it before treating the system as clean for public exposure.

## Git history warning

Removing a secret from the latest file does not remove it from old Git commits.

Before changing a previously private repository to Public, inspect the full history with a secret-scanning tool and rotate anything that may have been exposed.

## Repository scanner

Run:

```bash
python scripts/public-safety-check.py
```

The scanner checks common accidental-disclosure patterns. It is intentionally conservative and cannot guarantee that arbitrary secrets are absent.

See [docs/public-release-checklist.md](docs/public-release-checklist.md).
