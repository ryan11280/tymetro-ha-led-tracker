# Project Status

Last updated: **2026-08-22**

## Overall status

**V1 schedule tracker: functionally complete.**

The main end-to-end path is operational:

```text
TDX static timetable/runtime data
        ↓
Home Assistant static model
        ↓
python_script.tymetro_tracker (5 s)
        ↓
train objects + Frame A / Frame B
        ├──────────────→ Animated HA dashboard
        └──────────────→ ESPHome (600 ms renderer)
                               ↓
                         A1-A9 physical LEDs
```

The remaining work is primarily realtime validation and optional reliability/expansion work.

## Verified working end-to-end

### Physical hardware / ESPHome

- [x] NodeMCU v2 / ESP8266 online in ESPHome
- [x] NodeMCU USB-powered prototype
- [x] Breadboard powered from NodeMCU `3V3` / `GND`
- [x] MB102 power module removed from final prototype architecture
- [x] SN74HC595 controls A1–A8
- [x] GPIO16 / D0 controls A9
- [x] One 330 Ω resistor per LED
- [x] Individual LED output operation
- [x] `All LEDs On`
- [x] `All LEDs Off`
- [x] A1 → A9 → A1 chase test
- [x] Test actions temporarily pause the normal renderer and return control afterward
- [x] ESPHome subscribes to HA Frame A / Frame B sensors
- [x] ESPHome alternates frames every 600 ms
- [x] Station = stable LED
- [x] Between-station = adjacent-frame temporal animation
- [x] Multiple simultaneous train bits can be rendered

### Home Assistant schedule engine

- [x] Direction helper
- [x] Live Mode helper
- [x] 15-minute Live Session timer helper
- [x] TDX OAuth client-credentials token retrieval
- [x] Static `S2STravelTime` ingestion
- [x] Static `StoppingPattern` ingestion
- [x] A1 timetable ingestion
- [x] A8 timetable ingestion
- [x] Service-day selection
- [x] After-midnight operating-day handling
- [x] Local trajectory model
- [x] Express trajectory model
- [x] Express pass-through interpolation across skipped stations
- [x] Northbound A9 → A8 pre-anchor approach model
- [x] 5-second tracker recomputation
- [x] `sensor.tymetro_tracker`
- [x] `sensor.tymetro_led_frame_a`
- [x] `sensor.tymetro_led_frame_b`
- [x] Multi-train combination
- [x] Direction switching A1 / A9

### Dashboard

- [x] Custom Lovelace JavaScript card V2
- [x] A1–A9 fits on one desktop row
- [x] Smooth train-marker motion between 5-second tracker updates
- [x] Local / Express `普` / `直` markers
- [x] Multiple nearby markers vertically offset
- [x] Compact current-train progress list
- [x] Direction controls in the custom card
- [x] Live Mode control in the custom card
- [x] Schedule / Live / Stale status badges
- [x] Stale warning UI
- [x] Diagnostic footer

### Live data pipeline / safety behavior

- [x] LiveBoard is only polled while Live Mode is ON
- [x] Immediate LiveBoard fetch when Live Mode turns ON
- [x] 30-second LiveBoard polling cadence
- [x] 15-minute session limit configured
- [x] Live source freshness is based on source timestamps, not merely HTTP 200
- [x] Stale LiveBoard data is rejected by the tracker
- [x] Schedule mode remains active during stale LiveBoard conditions
- [x] `schedule_live_stale` state observed with genuinely stale TYMC upstream data
- [x] 40-second stale-abort automation is present in repository configuration

## Configured but not separately field-confirmed in this conversation

- [ ] Confirm the 40-second stale-abort automation actually toggles Live Mode OFF and creates the persistent notification on the running HA instance.
- [ ] Confirm HA-start Live Session reset behavior on the running instance after a real restart.

These are small acceptance tests, not blockers for normal Schedule mode.

## Implemented but awaiting fresh TYMC field validation

- [ ] LiveBoard-to-schedule event matching with a fresh source feed
- [ ] Local delay/early correction accuracy
- [ ] Express delay/early correction accuracy
- [ ] Correction stability across multiple LiveBoard refreshes
- [ ] Verify `live_correction_active = true` in normal fresh-feed operation

The matching code exists in `home-assistant/python_scripts/tymetro_tracker.py`. During the latest field test, Home Assistant successfully received HTTP 200 responses but TYMC `SrcUpdateTime` was more than 50 minutes old. The tracker correctly refused to apply that data.

## Reliability limitation

Schedule motion itself is local once `sensor.tymetro_static_model_raw` contains a valid model. However the current configuration refreshes static TDX data on HA startup and daily at 03:30.

A cold HA start during a complete TDX static-API outage has **not** been validated as an offline-cache scenario. Do not describe the current build as fully independent of TDX static APIs across arbitrary cold restarts.

See `docs/reliability.md`.

## V1 completion decision

The following can be treated as **finished for V1** unless the project scope changes:

- physical A1–A9 LED board
- ESPHome frame renderer
- schedule-based Home Assistant tracker
- direction switching
- Local / Express motion model
- animated Home Assistant UI

Future engineering work should focus on data quality, fresh LiveBoard validation, or deliberate hardware expansion rather than continuing to redesign the existing V1 UI/hardware without a new requirement.
