# Reliability Model

The project has two different dependency classes: **static schedule data** and **optional realtime data**.

## Schedule runtime

Once a valid `sensor.tymetro_static_model_raw` is available, train position calculations are local:

```text
static model
   ↓
python tracker every 5 s
   ↓
frames + dashboard
```

No TDX call occurs every 5 seconds.

## Static refresh dependency

The reference configuration refreshes the static model:

- on Home Assistant startup
- daily at 03:30

It fetches:

- S2STravelTime
- StoppingPattern
- A1 StationTimeTable
- A8 StationTimeTable

The current project has **not** field-validated a durable offline cache that guarantees recovery from a cold HA restart while all required TDX static endpoints are unavailable.

Therefore the correct reliability claim is:

> Schedule tracking operates autonomously after a valid static model has been loaded, but arbitrary cold-start independence from TDX static APIs is not yet guaranteed.

## LiveBoard dependency

LiveBoard is optional.

If Live Mode is OFF:

```text
LiveBoard request rate = zero
```

If Live Mode is ON:

- fetch immediately
- fetch every 30 seconds
- session limit = 15 minutes
- stale-source safety abort = configured after 40 seconds

Failure or staleness of LiveBoard does not stop Schedule mode.

## Data-quality rule

HTTP 200 does not mean realtime data is current.

The tracker checks source timestamps and accepts LiveBoard only when source age is within the configured freshness window (currently approximately 300 seconds).

The stale-feed field test demonstrated the desired safety behavior:

```text
HTTP request succeeds
      ↓
source timestamp is old
      ↓
schedule_live_stale
      ↓
no realtime correction
      ↓
schedule trajectory continues
```

## ESPHome / Home Assistant disconnect

The ESP8266 receives its frame values through the Home Assistant API integration.

If HA/API connectivity is interrupted, the microcontroller cannot calculate train schedules independently; it only owns the renderer. This is a deliberate architecture tradeoff that keeps the ESP8266 firmware simple.

A future “last-known animation” or autonomous embedded timetable mode would be a different architecture and is outside V1 scope.
