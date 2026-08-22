# Public Repository Checklist

The files in this repository are written to be sanitizable for a public portfolio / side-project repository.

Before changing the GitHub repository from **Private** to **Public**, perform all checks below.

## 1. Current working tree

Search for:

- TDX Client ID
- TDX Client Secret
- OAuth access tokens
- Home Assistant long-lived access tokens
- ESPHome API encryption keys
- Wi-Fi SSID/password
- ESPHome fallback AP passwords
- external Home Assistant URLs
- private IP addresses if you do not want network topology exposed
- personal email / address / phone number

Run the included sanity checker:

```bash
python scripts/public-safety-check.py
```

A clean result is useful but not proof that no secret exists.

## 2. Git history matters

Deleting a credential from the latest version does **not** remove it from earlier commits.

Before going public, inspect commit history or use a dedicated scanner such as:

```text
gitleaks
trufflehog
GitHub secret scanning
```

If a real credential has ever been committed, rotate it and clean/rewrite history if necessary.

## 3. Rotate previously exposed secrets

As a general security rule, rotate any secret that has ever been pasted into:

- chat
- issue
- gist
- screenshot
- log excerpt
- commit

This is true even if the current repository contains only placeholders.

## 4. Screenshot review

The included dashboard screenshot should be checked for:

- browser address bar / HA hostname
- local IP
- username
- notifications containing private information
- unrelated personal dashboards

The current packaged screenshot contains the tracker UI and generic dashboard tab labels; no credential is embedded in the image file by design.

## 5. `secrets.example.yaml` is safe only if it stays an example

It should look like:

```yaml
wifi_ssid: "YOUR_WIFI_SSID"
wifi_password: "YOUR_WIFI_PASSWORD"
tymetro_api_encryption_key: "GENERATE_A_NEW_ESPHOME_API_KEY"
tymetro_fallback_password: "CHANGE_ME"
```

Do not rename your actual secrets file into the repository.

## 6. Home Assistant snippet

The public configuration must reference:

```yaml
payload: !secret tdx_auth_payload
```

and must never embed the actual form payload.

## 7. License decision

A public GitHub repository is visible even without an open-source license.

- **No LICENSE file:** others can view the code, but you have not granted broad reuse rights.
- **MIT / Apache-2.0:** appropriate if you intentionally want others to reuse/modify the project.

This repository package does not automatically add an open-source license. Choose one deliberately if/when you want to.

## 8. TDX attribution / terms

The repository calls public TDX APIs but does not redistribute credentials. If you make the project public, keep the documentation clear that users need their own TDX credentials and should follow the current TDX service terms/quota policy.
