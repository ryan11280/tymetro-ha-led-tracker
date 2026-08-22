# Roadmap

## Near term

- Validate LiveBoard matching while TYMC realtime source is fresh.
- Compare calculated delay offsets with station ETA changes across several refreshes.
- Verify Local / Express matching at A3 and A8.
- Add clearer diagnostics for unmatched LiveBoard events.

## Data quality

- Evaluate TDX health metadata / source-health signaling without breaking the existing parser.
- Track both platform `UpdateTime` and source `SrcUpdateTime`.
- Consider adaptive stale thresholds only if justified by observed TYMC update cadence.

## Dashboard

Current V2 UI is intentionally stable for now.

Possible future additions:

- selected-train detail strip
- scheduled arrival time at next station
- realtime delay badge when correction is active
- expand A1–A9 to A1–A22 in the web UI
- optional simultaneous two-direction dashboard view

## Physical hardware

Possible future revisions:

- second LED row for the opposite direction
- additional shift registers for more stations
- PCB / perfboard build
- enclosure with printed A1–A9 station labels
- brightness control

The current breadboard design should remain the reference implementation because it is simple and easy to reproduce.
