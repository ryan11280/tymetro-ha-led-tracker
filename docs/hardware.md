# Physical LED Hardware

This document describes the **verified A1–A9 breadboard prototype** in enough detail to reproduce, debug, or later convert it to perfboard/PCB.

## 1. What the hardware represents

The physical board is a **position display**, not a literal station-stop board.

There is one LED for each physical station position from A1 through A9:

| LED | Station |
|---|---|
| A1 | Taipei Main Station / 台北車站 |
| A2 | Sanchong / 三重 |
| A3 | New Taipei Industrial Park / 新北產業園區 |
| A4 | Xinzhuang Fuduxin / 新莊副都心 |
| A5 | Taishan / 泰山 |
| A6 | Taishan Guihe / 泰山貴和 |
| A7 | National Taiwan Sport University / 體育大學 |
| A8 | Chang Gung Memorial Hospital / 長庚醫院 |
| A9 | Linkou / 林口 |

A train does not have to stop at a station for its physical position to pass that LED coordinate. Express trains are therefore interpolated through skipped station positions.

The board displays **one user-selected direction at a time**. Direction is chosen in Home Assistant; the LEDs themselves encode position only.

## 2. Verified prototype BOM

### Required parts used by the prototype

- 1 × NodeMCU v2 / ESP8266
- 1 × SN74HC595 8-bit shift register
- 9 × red 5 mm LEDs
- 9 × 330 Ω resistors
- 1 × solderless breadboard
- jumper wires
- USB cable / USB power for NodeMCU

### Not used in the final verified prototype

- MB102 breadboard power module

The final power path is:

```text
USB
 ↓
NodeMCU
 ├─ 3V3 ──> breadboard logic/LED supply
 └─ GND ──> breadboard ground
```

### Recommended optional improvement

A `0.1 µF / 100 nF / 104` ceramic capacitor directly across the SN74HC595 VCC/GND pins is good digital-logic decoupling practice.

**Important:** it is documented as a recommendation, not as a verified component of the original breadboard build unless you physically add it.

## 3. Why SN74HC595 + GPIO16

The SN74HC595 provides eight outputs while consuming only three ESP8266 control lines:

```text
DATA
CLOCK
LATCH
```

Those eight outputs map naturally to A1–A8.

A ninth output is still required for A9, so NodeMCU `D0 / GPIO16` directly drives A9.

```text
NodeMCU
  D7 / GPIO13 ---- DATA  -----┐
  D5 / GPIO14 ---- CLOCK -----┼--> SN74HC595 --> QA..QH --> A1..A8
  D6 / GPIO12 ---- LATCH -----┘

  D0 / GPIO16 ---------------------------------------> A9
```

## 4. LED electrical orientation

Every LED gets its **own** current-limiting resistor.

```text
GPIO/output
    │
    └──> LED anode (long leg)
          LED cathode (short leg)
                  │
                 330 Ω
                  │
                 GND
```

The outputs are active-high in ESPHome:

```text
output HIGH -> LED ON
output LOW  -> LED OFF
```

Do not place one resistor on a shared return for multiple LEDs; each LED needs an individual resistor.

At 3.3 V with a red LED and 330 Ω, LED current is only a few milliamps per channel. This is appropriate for a low-brightness indicator prototype. If the design grows into higher-current LEDs, multiple LEDs per station, long LED strips, or much higher brightness, use transistor/MOSFET drivers rather than loading the SN74HC595 directly.

## 5. Exact verified breadboard LED positions

The prototype LEDs were arranged along row `E`:

| Station | Anode / long leg | Cathode / short leg |
|---|---:|---:|
| A1 | E0 | E1 |
| A2 | E5 | E6 |
| A3 | E10 | E11 |
| A4 | E15 | E16 |
| A5 | E20 | E21 |
| A6 | E25 | E26 |
| A7 | E30 | E31 |
| A8 | E35 | E36 |
| A9 | E40 | E41 |

Each cathode column then connects through its own 330 Ω resistor to GND.

This spacing is not electrically required; it simply created a clean A1→A9 physical line on the prototype.

## 6. Exact verified SN74HC595 breadboard orientation

The IC straddles the breadboard center trench around columns 45–52.

Prototype orientation:

- **notch facing left**
- one side of the IC occupies `E45–E52`
- the opposite side occupies `F45–F52`

With that exact orientation:

```text
           notch / pin-1 end
                 ←

E45  pin16 VCC            pin1  QB   F45
E46  pin15 QA             pin2  QC   F46
E47  pin14 SER / DATA     pin3  QD   F47
E48  pin13 OE             pin4  QE   F48
E49  pin12 RCLK / LATCH   pin5  QF   F49
E50  pin11 SRCLK / CLOCK  pin6  QG   F50
E51  pin10 SRCLR / MR     pin7  QH   F51
E52  pin9  QH'            pin8  GND  F52
```

Always verify the physical IC notch/dot before trusting breadboard coordinates. Rotating the chip 180° changes every pin.

## 7. Complete SN74HC595 wiring table

| 74HC595 pin | Prototype coordinate | Signal | Connect to |
|---:|---|---|---|
| 16 | E45 | VCC | NodeMCU 3V3 |
| 15 | E46 | QA | A1 anode |
| 14 | E47 | SER / DATA | NodeMCU D7 / GPIO13 |
| 13 | E48 | OE | GND |
| 12 | E49 | RCLK / LATCH | NodeMCU D6 / GPIO12 |
| 11 | E50 | SRCLK / CLOCK | NodeMCU D5 / GPIO14 |
| 10 | E51 | SRCLR / MR | NodeMCU 3V3 |
| 9 | E52 | QH' serial out | not connected |
| 1 | F45 | QB | A2 anode |
| 2 | F46 | QC | A3 anode |
| 3 | F47 | QD | A4 anode |
| 4 | F48 | QE | A5 anode |
| 5 | F49 | QF | A6 anode |
| 6 | F50 | QG | A7 anode |
| 7 | F51 | QH | A8 anode |
| 8 | F52 | GND | GND |

### Control-pin rationale

- `OE` is active-low → tied to GND so outputs are always enabled.
- `SRCLR / MR` is active-low → tied to 3.3 V so the register is not asynchronously cleared.
- `QH'` is only required for cascading another shift register → unused in the single-register prototype.

## 8. NodeMCU pin map

| NodeMCU label | ESP8266 GPIO | Function |
|---|---:|---|
| D7 | GPIO13 | 74HC595 DATA |
| D5 | GPIO14 | 74HC595 CLOCK |
| D6 | GPIO12 | 74HC595 LATCH |
| D0 | GPIO16 | A9 direct LED output |
| 3V3 | — | breadboard / 74HC595 VCC |
| GND | — | common ground |

The matching ESPHome configuration is in [`../esphome/tymetro-led.yaml`](../esphome/tymetro-led.yaml).

## 9. Station output map

| Station | Hardware source | ESPHome output index |
|---|---|---:|
| A1 | 74HC595 QA | 0 |
| A2 | 74HC595 QB | 1 |
| A3 | 74HC595 QC | 2 |
| A4 | 74HC595 QD | 3 |
| A5 | 74HC595 QE | 4 |
| A6 | 74HC595 QF | 5 |
| A7 | 74HC595 QG | 6 |
| A8 | 74HC595 QH | 7 |
| A9 | NodeMCU GPIO16 | direct GPIO |

## 10. Power rules

### Verified simple topology

Use one source:

```text
USB -> NodeMCU -> 3V3/GND -> breadboard
```

### Ground is mandatory

The NodeMCU, 74HC595, and all LED cathode resistor returns must share the same GND reference.

### Breadboard split rails

Some breadboards split the red/blue rails in the middle. If you rely on the full rail length, verify continuity and bridge split sections with jumpers as needed.

### Do not casually add MB102 power

Do not simultaneously power the same 3.3 V rail from the NodeMCU and an unrelated breadboard supply unless the power architecture is deliberately redesigned. The MB102 is therefore not part of this reference build.

## 11. Hardware bring-up sequence

Do not start by debugging Home Assistant, TDX, ESPHome, and the breadboard at the same time.

Use this order:

### Stage A — power / polarity

1. USB-power the NodeMCU.
2. Confirm 3.3 V and GND rails.
3. Verify LED long/short leg orientation.
4. Verify every LED has its own resistor.

### Stage B — A9 direct GPIO

Test A9 independently.

Why first? It bypasses the 74HC595 and proves:

- ESP8266 GPIO switching
- LED polarity
- resistor path
- common GND

### Stage C — shift-register outputs

Test A1–A8 individually.

If A9 works and all A1–A8 fail, focus on the 74HC595 wiring rather than the common LED wiring.

### Stage D — full output tests

Run:

- `All LEDs Off`
- `All LEDs On`
- `LED Chase Test`

Expected chase:

```text
A1 -> A2 -> A3 -> A4 -> A5 -> A6 -> A7 -> A8 -> A9
A8 -> A7 -> A6 -> A5 -> A4 -> A3 -> A2 -> A1
```

### Stage E — Home Assistant renderer

Only after all nine physical outputs are known-good should Frame A / Frame B control be treated as the source of truth.

## 12. How the normal ESPHome renderer interacts with tests

The normal renderer runs every 600 ms.

Test buttons temporarily set:

```text
tymetro_renderer_paused = true
```

so the live HA frame renderer cannot immediately overwrite a manual test.

After the test delay/script finishes:

```text
tymetro_renderer_paused = false
```

and normal tracker control resumes automatically.

## 13. Troubleshooting decision tree

### Nothing lights

Check:

1. NodeMCU power
2. common GND
3. LED polarity
4. resistor path
5. ESPHome switch state

### A9 works, A1–A8 all fail

The shared LED/GND concept is probably okay. Check the shift register:

```text
pin16 VCC   -> 3.3V
pin8  GND   -> GND
pin10 SRCLR -> 3.3V
pin13 OE    -> GND
pin14 DATA  -> D7 / GPIO13
pin11 CLOCK -> D5 / GPIO14
pin12 LATCH -> D6 / GPIO12
```

Then verify IC orientation.

### A1–A8 operate but order is wrong

Check the QA→A1, QB→A2 ... QH→A8 mapping.

If the physical wiring is otherwise sound, output numbering can also be corrected in ESPHome.

### One LED never lights

Swap-test the LED/resistor or temporarily drive the corresponding output with another known-good LED. This isolates:

- dead LED
- reversed LED
- bad resistor connection
- broken jumper
- output mapping issue

### LEDs appear to flicker unexpectedly

First distinguish intentional frame animation from electrical instability.

Intentional station-between behavior alternates **specific adjacent stations at a stable 600 ms cadence**. Random or very fast flicker suggests wiring/power issues.

## 14. Physical display limitations

### One direction at a time

The single row cannot unambiguously encode both directions. HA selects the direction shown.

### Multiple trains at one position

LED bits are OR-combined. Two trains occupying the same represented station/segment do not create a “brighter two-train” state. The dashboard retains individual train objects and can distinguish them.

### Nine physical coordinates only

The current hardware covers A1–A9. Extending to A22 requires additional output hardware and a new physical layout.

## 15. Future hardware revisions

Reasonable next versions, only if there is a real requirement:

- second LED row for simultaneous opposite direction
- second SN74HC595 / daisy chain
- A1–A22 full-line board
- perfboard / custom PCB
- printed station labels
- enclosure
- transistor/MOSFET output stage for higher current
- brightness control through a suitable driver / PWM architecture

The existing breadboard build should remain the **reference V1 implementation** because it is easy to understand, reproduce, and debug.
