# Setup Guide

This guide assumes Home Assistant and ESPHome are already installed.

## 1. Assemble the hardware

Follow [hardware.md](hardware.md).

Do not proceed to TDX integration until all nine LEDs pass manual and chase tests.

## 2. Create Home Assistant helpers

Create the helpers exactly as documented in [../home-assistant/helpers.md](../home-assistant/helpers.md).

Expected entity IDs:

```text
input_select.tymetro_direction
input_boolean.tymetro_live_mode
timer.tymetro_live_session
```

## 3. Create TDX credentials

Create a TDX application and obtain:

- Client ID
- Client Secret

Add this to Home Assistant `secrets.yaml`:

```yaml
tdx_auth_payload: 'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET'
```

Keep the entire form body inside quotes.

## 4. Merge Home Assistant configuration

Use [../home-assistant/configuration-snippet.yaml](../home-assistant/configuration-snippet.yaml).

It contains these top-level keys:

```yaml
python_script:
recorder:
rest:
rest_command:
template:
```

If your existing `configuration.yaml` already has any of those keys, **merge the child entries**. Do not create duplicate top-level YAML keys.

Run:

```text
Developer Tools -> YAML -> Check configuration
```

before restarting Home Assistant.

## 5. Install the Python tracker

Copy:

```text
home-assistant/python_scripts/tymetro_tracker.py
```

to:

```text
/homeassistant/python_scripts/tymetro_tracker.py
```

After `python_script:` has been enabled and Home Assistant has restarted once, the action should appear as:

```text
python_script.tymetro_tracker
```

Execute it manually once in Developer Tools.

Expected output entities:

```text
sensor.tymetro_tracker
sensor.tymetro_led_frame_a
sensor.tymetro_led_frame_b
```

## 6. Add automations

Create three Home Assistant automations using the files in:

```text
home-assistant/automations/
```

### Live Session Control

Starts/cancels the 15-minute timer and automatically switches Live Mode off when the timer ends.

### Tracker Engine

Runs the Python tracker every 5 seconds and immediately after relevant state changes.

This does **not** call TDX every 5 seconds. It only recalculates from already-ingested Home Assistant state.

### Abort Stale Live

If Live Mode was enabled but the TDX source remains stale after 40 seconds, turns Live Mode off and shows a persistent notification.

## 7. Flash ESPHome

Copy [../esphome/tymetro-led.yaml](../esphome/tymetro-led.yaml) into ESPHome Device Builder.

Create secrets based on [../esphome/secrets.example.yaml](../esphome/secrets.example.yaml).

Validate first, then install via USB or OTA.

Verify:

- device connects to Home Assistant Native API
- `sensor.tymetro_led_frame_a` and `sensor.tymetro_led_frame_b` are visible to ESPHome
- physical LEDs follow the tracker automatically

## 8. Install the dashboard card

Copy:

```text
dashboard/tymetro-tracker-card.js
```

to:

```text
/homeassistant/www/tymetro-tracker-card.js
```

Add a Lovelace resource:

```text
/local/tymetro-tracker-card.js?v=2
```

Resource type:

```text
JavaScript Module
```

When replacing the JavaScript file, increment the `?v=` query string to avoid browser cache confusion.

## 9. Add the dashboard view

Use [../dashboard/view.yaml](../dashboard/view.yaml).

The card directly controls:

- direction selector
- Live Mode

and reads:

- tracker train objects
- timer
- static model status
- LiveBoard status

## 10. Validate schedule mode

With Live Mode OFF:

1. Switch to `← 往 A1 台北`.
2. Confirm train list and animated markers update.
3. Switch to `往 A9 林口 →`.
4. Confirm physical LEDs change direction representation.
5. Confirm `updated_at` changes roughly every 5 seconds.

## 11. Validate Live Mode

Enable Live Mode.

Expected healthy path:

```text
Live ON
-> LiveBoard fetch
-> schedule_live_pending
-> matching succeeds
-> live
-> live_correction_active = true
```

Expected stale path:

```text
Live ON
-> LiveBoard fetch returns old SrcUpdateTime
-> schedule_live_stale
-> schedule display continues
-> after ~40 s Live Mode automatically turns OFF
```

Do not increase the stale threshold simply to make the UI say `live`. Old ETA data is worse than a clearly labeled schedule fallback.
