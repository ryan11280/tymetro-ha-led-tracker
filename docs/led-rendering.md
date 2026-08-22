# LED Rendering Model

This document explains how continuous train position becomes a 9-LED physical display.

## 1. Inputs

The Home Assistant tracker emits:

```text
sensor.tymetro_led_frame_a
sensor.tymetro_led_frame_b
```

Each state is an integer from `0` to `511` (`2^9 - 1`).

Each bit maps to one physical station coordinate:

```text
bit:   8 7 6 5 4 3 2 1 0
LED:   A9 A8 A7 A6 A5 A4 A3 A2 A1
```

## 2. Why two frames

Nine LEDs cannot directly show a train at 53% between two stations.

The tracker therefore translates continuous motion into two temporal frames.

For A5 → A6:

### First third

```text
progress < 0.333

Frame A: A5
Frame B: A5
```

The train still visually belongs to A5.

### Middle third

```text
0.333 <= progress < 0.667

Frame A: A5
Frame B: A6
```

ESPHome alternates the two LEDs, visually communicating that the train is between the stations.

### Final third

```text
progress >= 0.667

Frame A: A6
Frame B: A6
```

The train has visually advanced to A6.

## 3. At a station

A stationary / dwelling train uses the same bit in both frames:

```text
Frame A = A3
Frame B = A3
```

The LED therefore appears continuously lit.

## 4. ESPHome timing

The ESP8266 alternates frame phase every:

```text
600 ms
```

This animation is local to the microcontroller.

Home Assistant only needs to update the two integer frame states whenever the trajectory engine changes them, rather than sending nine switch operations every 600 ms.

## 5. Multiple trains

All represented train bits are OR-combined into each frame.

Example:

```text
Train 1: stable A1
Train 2: middle A4 -> A5
Train 3: stable A8

Frame A: A1 + A4 + A8
Frame B: A1 + A5 + A8
```

This was exercised in the real ESPHome renderer with more than one simultaneous station-between animation.

## 6. Direction

Direction is **not encoded in the LED pattern**.

The user first selects one direction in Home Assistant:

```text
← 往 A1 台北
```

or:

```text
往 A9 林口 →
```

The tracker then generates frames only for that direction.

This avoids trying to express too many semantics with a single LED row.

## 7. Local vs Express

The hardware does not blink differently for Local vs Express.

That choice is intentional:

- physical LEDs = position
- Home Assistant dashboard = richer train metadata

The dashboard can label trains `普` or `直`, but the physical board remains readable and simple.

## 8. Express trains at skipped stations

An Express service can pass a physical station coordinate without stopping there.

The trajectory engine estimates pass-through time using the physical segment proportions derived from the Local runtime model, then renders the Express train along the same A1–A9 coordinate line.

Therefore an A2 LED can briefly represent an Express train **passing the A2 physical position**, even though A2 is not an Express stop.

## 9. Hardware vs dashboard semantics

The dashboard intentionally does **not** mimic the physical two-frame limitation.

The custom card receives continuous `from`, `to`, and `progress` values and places a train marker at an interpolated screen coordinate:

```text
x = from_x + progress × (to_x - from_x)
```

CSS transitions then tween the marker smoothly until the next 5-second tracker update.

This produces two different but consistent renderers from the same train model:

```text
canonical train model
       ├── physical renderer -> 9 LEDs + temporal frames
       └── dashboard renderer -> smooth continuous position
```
