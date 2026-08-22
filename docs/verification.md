# Verification / Acceptance Tests

Use this document to distinguish code that exists from behavior that has actually been exercised.

## A. Physical output acceptance

### A1–A9 channel test

Expected:

- every LED can be turned on/off
- no output is swapped
- no LED depends on another LED's resistor

Status: **verified**

### All LEDs On / Off

Expected:

```text
All LEDs On  -> A1..A9 all on briefly
All LEDs Off -> A1..A9 all off briefly
```

Renderer control resumes afterward.

Status: **verified**

### Chase

Expected:

```text
A1 -> A2 -> A3 -> A4 -> A5 -> A6 -> A7 -> A8 -> A9
A8 -> A7 -> A6 -> A5 -> A4 -> A3 -> A2 -> A1
```

Status: **verified**

## B. Home Assistant → ESPHome integration

Expected ESPHome API subscription to:

```text
sensor.tymetro_led_frame_a
sensor.tymetro_led_frame_b
```

Status: **verified**

## C. Frame renderer

Expected:

- station bit stable in Frame A and B
- middle-third segment alternates adjacent station bits
- phase toggles every ~600 ms

Status: **verified**

Multiple simultaneous station-between animations were observed on the physical renderer.

## D. Schedule tracker

Expected:

- `sensor.tymetro_tracker` updates every ~5 s
- `frame_a` / `frame_b` stay in 0..511
- selected direction changes train set
- Local and Express trains are modeled
- multiple trains can be visible simultaneously

Status: **verified**

## E. Animated dashboard

Expected:

- A1–A9 fit in one desktop line
- train markers are derived from `from`, `to`, `progress`
- markers transition smoothly between tracker refreshes
- multiple nearby trains offset vertically
- current-train list agrees with marker positions

Status: **verified**

## F. LiveBoard ingestion

Expected:

- no polling while Live Mode OFF
- immediate request when Live Mode ON
- subsequent request every 30 s
- response records filtered to A1–A9

Status: **verified**

## G. LiveBoard stale protection

Observed case:

- HA `fetched_at` was current
- HTTP status was 200
- newest TYMC source timestamp was more than 50 minutes old

Expected tracker result:

```text
mode = schedule_live_stale
live_correction_active = false
```

Schedule positions continue.

Status: **verified**

## H. 40-second stale auto-abort

Expected:

1. turn Live Mode ON
2. tracker remains `schedule_live_stale`
3. wait ~40 s
4. `input_boolean.tymetro_live_mode` turns OFF
5. persistent notification is created

Status: **automation configured; final running-instance acceptance not reported yet**

## I. Fresh LiveBoard correction

Expected healthy path:

```text
Live ON
 -> fresh LiveBoard
 -> schedule_live_pending
 -> conservative match succeeds
 -> live
 -> live_correction_active = true
 -> one or more trains live_corrected = true
```

Status: **pending fresh TYMC source feed**

## J. Cold-start TDX static outage

Expected desired future property:

```text
HA cold restart while TDX static APIs unavailable
 -> restore/use cached static model
 -> Schedule tracker still starts
```

Status: **not a verified V1 feature**
