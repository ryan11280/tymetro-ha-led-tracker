# Troubleshooting

## Home Assistant / ESPHome API

### `BAD_INDICATOR` in ESPHome Native API logs

Typical cause: Home Assistant has an old Noise encryption key stored for the device.

Fix:

1. Remove only the Home Assistant ESPHome integration entry for the device.
2. Add it again using the current device IP / hostname.
3. Enter the current API encryption key.

Do not delete the ESPHome YAML just to fix an integration-key mismatch.

## ESP8266 flashing warning

A warning similar to:

```text
Failed to communicate with the flash chip...
```

can appear even when erase/write/boot ultimately succeed. If the firmware writes to 100%, boots, joins Wi-Fi, and ESPHome logs are normal, it is not necessarily blocking.

If future flashing actually fails, disconnect hardware from sensitive GPIOs and retry USB flashing.

## LEDs

### A9 works but A1–A8 do not

Check the 74HC595 power/control pins and IC orientation. See [hardware.md](hardware.md).

### A1–A8 are in the wrong order

Fix the `number:` mapping under the ESPHome `switch:` entities. Rewiring is usually unnecessary.

### Chase test is interrupted by the tracker

The provided ESPHome YAML pauses the renderer during test buttons/scripts and restores tracker control afterward.

## Python Script

### `TypeError: isinstance() arg 2 must be a type...`

Home Assistant `python_script` runs in a restricted environment. An earlier development version used `isinstance(..., list/dict)` in a way that was incompatible with that sandbox.

The repository version avoids that pattern. Use the current `tymetro_tracker.py`.

## TDX

### HTTP 200 but tracker says `schedule_live_stale`

This is expected if the source timestamp is old.

Check:

- Home Assistant `fetched_at`
- LiveBoard `UpdateTime`
- LiveBoard `SrcUpdateTime`

If `fetched_at` is current but `SrcUpdateTime` is tens of minutes old, Home Assistant is polling correctly and the upstream feed itself is stale.

Do not treat HTTP 200 as realtime health.

### Tracker stays `schedule_live_pending`

Possible causes:

- LiveBoard is fresh but no schedule event matches confidently
- destination/pattern combination is ambiguous
- the relevant train is outside the modeled A1–A9 window

Inspect these attributes:

```text
live_source_age_seconds
live_match_count
live_matched_event_count
corrected_train_count
live_corrections
```

## Dashboard custom card

### `Custom element doesn't exist: tymetro-tracker-card`

Verify:

1. JS file exists at `/homeassistant/www/tymetro-tracker-card.js`.
2. Resource is registered as `/local/tymetro-tracker-card.js?v=N`.
3. Resource type is JavaScript Module.
4. Hard-refresh the browser.

Increment `?v=N` whenever replacing the JS file.

### Old UI still appears

Usually browser/Lovelace resource caching. Increment the resource query string and hard-refresh.
