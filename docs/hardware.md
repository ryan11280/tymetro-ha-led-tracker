# Hardware

## Final prototype design

- NodeMCU v2 / ESP8266
- SN74HC595 shift register for A1–A8
- GPIO16 / D0 directly drives A9
- 9 × red 5 mm LEDs
- 9 × 330 Ω current-limiting resistors
- 0.1 µF ceramic decoupling capacitor near the SN74HC595
- USB powers the NodeMCU
- NodeMCU `3V3` and `GND` power the breadboard rails

The MB102 breadboard power module is **not used** in the final prototype.

## SN74HC595 wiring

| 74HC595 pin | Name | Connection |
|---|---|---|
| 16 | VCC | NodeMCU 3V3 |
| 15 | QA | A1 LED anode |
| 1 | QB | A2 LED anode |
| 2 | QC | A3 LED anode |
| 3 | QD | A4 LED anode |
| 4 | QE | A5 LED anode |
| 5 | QF | A6 LED anode |
| 6 | QG | A7 LED anode |
| 7 | QH | A8 LED anode |
| 8 | GND | GND |
| 9 | QH' | Not connected |
| 10 | SRCLR / MR | 3V3 |
| 11 | SRCLK / CLOCK | NodeMCU D5 / GPIO14 |
| 12 | RCLK / LATCH | NodeMCU D6 / GPIO12 |
| 13 | OE | GND |
| 14 | SER / DATA | NodeMCU D7 / GPIO13 |

A9 LED anode is connected directly to NodeMCU `D0 / GPIO16`.

## LED wiring

Every LED uses its own resistor:

```text
output/GPIO -> LED anode (long leg)
LED cathode (short leg) -> 330 Ω -> GND
```

Do not share one resistor between multiple LEDs.

## Prototype breadboard positions

The physical prototype used LEDs on row E, each spanning two numbered breadboard columns:

| Station | Anode | Cathode |
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

Cathode columns connect through individual 330 Ω resistors to GND.

The SN74HC595 straddled the center trench around columns 45–52 with the notch facing left in the prototype layout. Pin numbering should always be verified from the IC orientation rather than relying only on breadboard column numbers.

## Power rails

If the breadboard power rails are split in the middle, bridge both 3.3 V sections and both GND sections with jumper wires.

Use one power source for this prototype:

```text
USB -> NodeMCU -> 3V3/GND -> breadboard
```

Do not simultaneously power the rail from a separate breadboard supply unless the power architecture is intentionally redesigned.

## Decoupling

Place a `0.1 µF / 104` ceramic capacitor close to the 74HC595 between VCC and GND.

## Expected current

With 3.3 V logic and 330 Ω resistors, each red LED is only a few milliamps. This is appropriate for the current single-LED-per-output prototype. If the project is expanded to higher-current LEDs, multiple LEDs per output, or higher brightness, add proper transistor/MOSFET drivers rather than increasing current through the 74HC595.

## Hardware test sequence

Before connecting tracker logic:

1. Confirm NodeMCU boots and joins Wi-Fi.
2. Confirm A9 can be switched independently; this validates basic LED polarity/GND wiring without the shift register.
3. Test A1–A8 individually.
4. Run `All LEDs On`.
5. Run the A1→A9→A1 chase test.
6. Only after all nine channels work, enable the Home Assistant frame renderer.

## Troubleshooting by symptom

### A9 fails, A1–A8 may also fail

Check common LED orientation, 330 Ω resistor path, GND rail, and NodeMCU power.

### A9 works, all A1–A8 fail

Focus on the SN74HC595:

- pin 16 = 3.3 V
- pin 8 = GND
- pin 10 = 3.3 V
- pin 13 = GND
- data = GPIO13 / D7
- clock = GPIO14 / D5
- latch = GPIO12 / D6
- verify IC notch orientation

### A1–A8 light in the wrong order

The output mapping can be corrected in ESPHome without physically rewiring every LED.
