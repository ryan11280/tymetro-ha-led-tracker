# Security Notes

This repository is designed to contain only sanitized configuration.

## Never commit

- TDX Client ID
- TDX Client Secret
- TDX access tokens
- Home Assistant long-lived access tokens
- ESPHome Native API encryption keys
- Wi-Fi SSID/password if sensitive
- ESPHome fallback hotspot passwords
- Any externally reachable Home Assistant URL or credential

## Home Assistant secrets

The project expects a TDX auth payload in Home Assistant `secrets.yaml`:

```yaml
tdx_auth_payload: 'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET'
```

The value must be quoted because the form body contains `&` characters.

## ESPHome secrets

Copy `esphome/secrets.example.yaml` to your own ESPHome secrets file and replace all placeholders.

## Rotate previously exposed credentials

If a secret has ever been pasted into a chat, screenshot, issue, gist, or commit, treat it as exposed and rotate it even if this repository is private.

## Repository visibility

The project currently targets a private GitHub repository. Private visibility is still not a substitute for proper secret handling.
