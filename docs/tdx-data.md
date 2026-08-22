# TDX Data Model and API Strategy

## Authentication

The project uses the TDX OAuth client-credentials flow.

Home Assistant stores only the returned access token in `sensor.tdx_token`; the Client ID and Client Secret remain in `secrets.yaml`.

## Static APIs

These are used to build the deterministic schedule model:

### `Rail/Metro/S2STravelTime/TYMC`

Provides travel-time models including `TrainType`, station-to-station `RunTime`, and related timing information.

### `Rail/Metro/StoppingPattern/TYMC`

Describes stopping patterns used to distinguish Local / Express / special variants.

### `Rail/Metro/StationTimeTable/TYMC`

The project currently pulls A1 and A8 anchor timetables.

Timetable records provide fields such as:

- `Direction`
- `DestinationStationID` / legacy typo `DestinationStaionID`
- `TrainType`
- `StoppingPatternID`
- `ArrivalTime`
- `DepartureTime`
- `ServiceDay`

## Live API

### `Rail/Metro/LiveBoard/TYMC`

Typical record fields observed:

```yaml
StationID: A2
TripHeadSign: 往台北車站
DestinationStationID: A1
ServiceStatus: 0
EstimateTime: 7
SrcUpdateTime: '2026-08-22T21:39:04+08:00'
UpdateTime: '2026-08-22T21:40:34+08:00'
```

Important: this is **station-centric ETA data**, not a train GPS feed.

A station can simultaneously contain several ETA rows for upcoming trains. The payload does not reliably provide a unique physical train ID suitable for direct position tracking.

## Why schedule is the backbone

Because LiveBoard is not GPS, the project first generates a schedule trajectory for each train. LiveBoard events then act as observations that can shift those timelines early or late.

This creates two useful properties:

1. The display still works when realtime data is unavailable.
2. Realtime data cannot force impossible train motion if the feed is incomplete or ambiguous.

## Freshness protection

A successful HTTP response is not sufficient proof of realtime quality.

During field testing, Home Assistant fetched LiveBoard successfully at approximately 22:43 while the latest TYMC `SrcUpdateTime` was still around 21:47. The source was therefore more than 50 minutes stale even though HTTP status remained 200.

The tracker currently treats LiveBoard as fresh only when source age is within approximately 5 minutes.

When stale:

```text
mode = schedule_live_stale
live_correction_active = false
```

The physical display continues using schedule data.

A separate automation waits 40 seconds after Live Mode is enabled and automatically turns Live Mode off if the tracker remains stale.

## Request strategy

### Normal operation

Live Mode OFF:

- zero LiveBoard polling
- schedule tracker runs locally every 5 seconds

### Static refresh

- startup
- once daily at 03:30

### Live session

- one immediate LiveBoard fetch
- one fetch every 30 seconds
- maximum session duration: 15 minutes
- early abort after 40 seconds if source remains stale

This keeps request volume intentionally low.

## Service status

Observed/used behavior treats `ServiceStatus: 0` as normal service. Non-normal records are excluded from Live matching.

## Token refresh behavior

TDX determines the actual token lifetime through the OAuth response `expires_in` value. The Home Assistant reference configuration stores that value and refreshes the REST token entity on a conservative 12-hour scan interval; it does not rely on a hard-coded claim that TDX tokens always last a particular number of hours.
