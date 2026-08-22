# Changelog

## 2026-08-22 — V1 repository baseline

### Added / completed

- A1–A9 schedule trajectory tracker in Home Assistant
- Local and Express motion models
- 5-second local tracker engine
- two-frame 9-bit LED position model
- ESPHome 600 ms renderer
- NodeMCU + SN74HC595 physical 9-LED prototype
- A1–A8 shift-register outputs + A9 direct GPIO16 output
- All On / Off and chase-test controls
- direction selector
- 15-minute Live Mode session control
- TDX static model ingestion
- TDX LiveBoard ingestion
- LiveBoard freshness validation and schedule fallback
- stale Live Mode abort automation
- animated Lovelace custom card V2
- deployment, architecture, hardware, troubleshooting, and security documentation

### Validation state

- Schedule path verified end-to-end.
- Physical LED path verified end-to-end.
- Dashboard verified with multiple trains.
- LiveBoard stale-data rejection verified.
- LiveBoard fresh-feed train matching remains pending field validation because the TYMC source was stale during the latest test.

### Documentation correction

- Hardware documentation now distinguishes the **verified prototype** from optional electrical improvements such as a local `0.1 µF` decoupling capacitor. The capacitor is recommended practice but is not claimed as part of the verified breadboard build unless actually installed.
