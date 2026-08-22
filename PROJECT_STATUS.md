# Project Status

Last updated: 2026-08-22

## Working end-to-end

- [x] NodeMCU v2 / ESP8266 online in ESPHome
- [x] SN74HC595 controls A1–A8 LEDs
- [x] GPIO16 controls A9 LED
- [x] All LEDs On / Off test
- [x] A1 → A9 → A1 chase test
- [x] Home Assistant direction selector
- [x] Home Assistant Live Mode helper
- [x] 15-minute Live Mode session timer
- [x] TDX OAuth client-credentials token retrieval
- [x] TDX static data ingestion
- [x] Schedule-based train trajectory engine
- [x] Local / Express schedule modeling
- [x] 5-second tracker recomputation
- [x] Frame A / Frame B output
- [x] ESPHome 600 ms frame renderer
- [x] Multiple simultaneous trains displayed
- [x] Direction switching A1 / A9
- [x] Animated Lovelace custom card
- [x] LiveBoard polling only while Live Mode is enabled
- [x] LiveBoard stale-data protection
- [x] Automatic Live Mode abort when stale

## Implemented but still being validated

- [ ] TDX LiveBoard-to-schedule event matching in normal fresh-feed conditions
- [ ] Delay/early correction accuracy across Local and Express services
- [ ] Realtime correction persistence across multiple LiveBoard refreshes

The matching code exists in `home-assistant/python_scripts/tymetro_tracker.py`. During the most recent field test, the TYMC source feed was over 50 minutes stale even though HTTP returned 200, so the safety path correctly produced `schedule_live_stale` instead of applying false realtime corrections.

## Current UI

Dashboard custom card V2:

- A1–A9 fit on one desktop row
- Train markers animate between stations
- Multiple trains are vertically offset when close together
- Local / Express shown as `普` / `直`
- Compact progress list
- Schedule / Live / Stale state badges
- Direction and Live controls built into the card

## Current hardware scope

Only A1–A9 and one selected direction are shown on the physical LED row. The dashboard is not limited by the nine-LED representation.
