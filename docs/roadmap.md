# Roadmap

## V1 — considered complete

The following areas are intentionally frozen unless a new requirement appears:

- A1–A9 breadboard hardware
- NodeMCU + single SN74HC595 architecture
- one selected physical direction
- ESPHome 600 ms two-frame renderer
- schedule trajectory engine
- Local / Express schedule modeling
- animated Lovelace V2 UI

## Realtime / data-quality work

Priority items:

- validate LiveBoard matching while TYMC source data is genuinely fresh
- compare correction offsets over several consecutive LiveBoard refreshes
- validate Local matching
- validate Express matching, especially around A3 / A8
- confirm correction persistence and handoff behavior
- add more diagnostics only if field validation reveals ambiguity

## Reliability work

Optional future hardening:

- implement and field-test durable static-model caching for TDX-unavailable cold starts
- expose a clear “static model age” diagnostic
- test HA restart during TDX outage
- test ESPHome reconnect behavior after prolonged HA outage

Do not claim offline cold-start support until it is actually tested.

## Dashboard ideas

The current UI is considered sufficient for V1.

Possible future improvements:

- selected-train detail strip
- scheduled next-station time
- realtime delay badge
- simultaneous two-direction web view
- A1–A22 expansion

## Physical hardware ideas

Only pursue if the project scope changes:

- second LED row for opposite direction
- daisy-chain another SN74HC595
- full A1–A22 physical map
- perfboard / PCB
- enclosure / printed labels
- higher-current output drivers
- brightness control
