# 實體 LED 硬體

本文件完整記錄目前已實際驗證的 **A1～A9 Breadboard 實體 LED 原型**。

目標是即使過一段時間重新拆裝，也能依本文件重新搭建。

---

# 1. 最終原型架構

```text
                         ┌──────────────────────────────┐
                         │        NodeMCU v2            │
                         │         ESP8266              │
                         │                              │
Home Assistant Frames ──→│ ESPHome 600ms Renderer      │
                         │                              │
                         │ D7 GPIO13 ─ DATA ─────┐      │
                         │ D5 GPIO14 ─ CLOCK ────┼──┐   │
                         │ D6 GPIO12 ─ LATCH ────┘  │   │
                         │                          ▼   │
                         │                    SN74HC595 │
                         │                  QA ... QH   │
                         │                   │     │    │
                         │                   A1   A8    │
                         │                              │
                         │ D0 GPIO16 ─────────────→ A9  │
                         └──────────────────────────────┘
```

A1～A8 使用 SN74HC595。

A9 使用 NodeMCU `D0 / GPIO16`。

---

# 2. 元件清單

| 元件 | 數量 | 說明 |
|---|---:|---|
| NodeMCU v2 / ESP8266 | 1 | ESPHome 主控制器 |
| SN74HC595 | 1 | 8-bit serial-in / parallel-out 移位暫存器 |
| 5 mm 紅色 LED | 9 | A1～A9 |
| 330 Ω 電阻 | 9 | 每顆 LED 一顆 |
| Breadboard | 1 | 原型 |
| Jumper Wire | 多條 | 接線 |
| USB Cable | 1 | NodeMCU 供電 |

### 建議但目前不列入「已驗證原型」的元件

- 0.1 µF ceramic capacitor，放在 74HC595 VCC / GND 附近作去耦

這是良好數位電路習慣，但目前 Breadboard 原型即使沒有它也已經正常運作，因此文件不把它寫成現有硬體的一部分。

---

# 3. 供電

目前原型：

```text
USB
 ↓
NodeMCU
 ├─ 3V3 → Breadboard 3.3V
 └─ GND → Breadboard GND
```

SN74HC595 與 LED 使用同一組 3.3 V / GND reference。

目前不使用 MB102 Breadboard Power Supply。

---

# 4. LED 極性

一般 5 mm LED：

```text
長腳 = Anode / 正極
短腳 = Cathode / 負極
```

本專案統一：

```text
Output
  ↓
LED Anode 長腳
  ↓
LED
  ↓
LED Cathode 短腳
  ↓
330 Ω
  ↓
GND
```

所以 GPIO / 74HC595 output 為 HIGH 時 LED 亮。

---

# 5. 為什麼每顆 LED 都要一顆 330 Ω？

每個 LED 都是獨立 branch。

正確：

```text
QA → LED A1 → 330Ω → GND
QB → LED A2 → 330Ω → GND
QC → LED A3 → 330Ω → GND
...
```

不要：

```text
多顆 LED
   ↓
共用一顆 330Ω
   ↓
GND
```

因為不同 LED 同時點亮時會互相影響電流。

---

# 6. A1～A9 Breadboard 位置

目前實際搭建位置：

| 站 | 長腳 / Anode | 短腳 / Cathode |
|---|---|---|
| A1 | E0 | E1 |
| A2 | E5 | E6 |
| A3 | E10 | E11 |
| A4 | E15 | E16 |
| A5 | E20 | E21 |
| A6 | E25 | E26 |
| A7 | E30 | E31 |
| A8 | E35 | E36 |
| A9 | E40 | E41 |

也就是每站間隔約 5 格：

```text
A1     A2     A3     A4     A5     A6     A7     A8     A9
E0     E5     E10    E15    E20    E25    E30    E35    E40
```

視覺上就形成一條 A1～A9 的車站線。

每顆 LED：

```text
Anode → 前一格
Cathode → 後一格 → 330Ω → GND
```

---

# 7. SN74HC595 放置方向

目前 IC 跨 Breadboard 中央溝槽：

```text
E45 ～ E52
F45 ～ F52
```

IC 缺口朝左。

從上方看：

```text
             缺口
              ◀

      E side             F side

E45  pin16 VCC       pin1  QB   F45
E46  pin15 QA        pin2  QC   F46
E47  pin14 SER       pin3  QD   F47
E48  pin13 OE        pin4  QE   F48
E49  pin12 RCLK      pin5  QF   F49
E50  pin11 SRCLK     pin6  QG   F50
E51  pin10 SRCLR     pin7  QH   F51
E52  pin9  QH'       pin8  GND  F52
```

**接線前一定先確認缺口方向。**

74HC595 左右顛倒時，pin number 會全部錯位。

---

# 8. SN74HC595 完整接線

## Power / Control

| Pin | 名稱 | 接法 |
|---:|---|---|
| 16 | VCC | 3.3 V |
| 15 | QA | A1 |
| 14 | SER / DATA | NodeMCU D7 / GPIO13 |
| 13 | OE | GND |
| 12 | RCLK / LATCH | NodeMCU D6 / GPIO12 |
| 11 | SRCLK / CLOCK | NodeMCU D5 / GPIO14 |
| 10 | SRCLR / MR | 3.3 V |
| 9 | QH' | 不接 |
| 8 | GND | GND |

## Output

| Pin | Output | 車站 |
|---:|---|---|
| 15 | QA | A1 |
| 1 | QB | A2 |
| 2 | QC | A3 |
| 3 | QD | A4 |
| 4 | QE | A5 |
| 5 | QF | A6 |
| 6 | QG | A7 |
| 7 | QH | A8 |

A9：

```text
NodeMCU D0 / GPIO16 → A9
```

---

# 9. NodeMCU 使用的 GPIO

| NodeMCU Label | GPIO | 用途 |
|---|---:|---|
| D7 | GPIO13 | 74HC595 DATA |
| D5 | GPIO14 | 74HC595 CLOCK |
| D6 | GPIO12 | 74HC595 LATCH |
| D0 | GPIO16 | A9 LED |

所以只使用 4 個 NodeMCU GPIO 就完成 9 顆 LED。

---

# 10. 為什麼 OE 要接 GND？

74HC595：

```text
OE = Output Enable
```

它是 Active-Low。

因此：

```text
OE = LOW
```

output 才會正常輸出。

本專案直接：

```text
pin 13 OE → GND
```

---

# 11. 為什麼 SRCLR 要接 3.3 V？

`SRCLR` / `MR` 是 Active-Low reset。

如果拉低：

```text
Shift Register data 被清空
```

因此正常使用固定：

```text
pin 10 SRCLR → 3.3V
```

避免浮動。

---

# 12. ESPHome Output Mapping

A1～A8：

```yaml
pin:
  sn74hc595: tymetro_595
  number: 0..7
```

對應：

```text
number 0 = QA = A1
number 1 = QB = A2
...
number 7 = QH = A8
```

A9：

```yaml
pin:
  number: GPIO16
```

---

# 13. 開機安全狀態

所有 LED switch：

```yaml
restore_mode: ALWAYS_OFF
```

目的：

> NodeMCU 剛開機或 HA 還沒連線時，不要保留上一次的燈號。

---

# 14. 硬體測試順序

建議每次重新搭建後按照以下順序驗證。

## Step 1：確認電源

確認：

```text
NodeMCU 3V3 → 74HC595 VCC
NodeMCU GND → 74HC595 GND
所有 LED resistor → 同一個 GND
```

## Step 2：All LEDs Off

ESPHome：

```text
All LEDs Off
```

預期：

```text
A1～A9 全暗
```

## Step 3：All LEDs On

```text
All LEDs On
```

預期：

```text
A1～A9 全亮
```

這可以快速確認：

- LED 極性
- resistor
- output
- A9 GPIO16
- 595 八個 channel

## Step 4：Chase Test

```text
A1
 ↓
A2
 ↓
A3
 ↓
...
 ↓
A9
 ↓
A8
 ↓
...
 ↓
A1
```

如果順序正確，表示 QA～QH mapping 正確。

## Step 5：接回 HA Frame

確認 ESPHome log 有：

```text
sensor.tymetro_led_frame_a
sensor.tymetro_led_frame_b
```

並開始隨 Tracker 更新。

---

# 15. Test Button 為什麼要 Pause Renderer？

如果 ESPHome 正常 renderer 每 600 ms 都在更新 LED，而同時按：

```text
All LEDs On
```

renderer 下一輪可能馬上又把燈改回 HA Frame。

所以測試時：

```text
tymetro_renderer_paused = true
```

先暫停正常 renderer。

測試完成後：

```text
tymetro_renderer_paused = false
```

再交還 Frame A / B 控制。

---

# 16. 600 ms Renderer

ESPHome 每 600 ms 執行：

```text
Frame A
 ↓
Frame B
 ↓
Frame A
 ↓
Frame B
```

每次把 9-bit mask 拆成：

```text
bit0 → A1
bit1 → A2
...
bit8 → A9
```

然後只在狀態真的改變時呼叫：

```text
turn_on()
turn_off()
```

避免無意義的重複 output。

---

# 17. 多班列車

例如同時有：

```text
Train 1 在 A2
Train 2 在 A6
Train 3 在 A8→A9 中間
```

Tracker 會把所有 bit OR 起來。

例如某一 frame：

```text
A2 = ON
A6 = ON
A8 = ON
```

另一 frame：

```text
A2 = ON
A6 = ON
A9 = ON
```

所以實體 LED 能同時表示多班列車。

---

# 18. 直達車經過不停靠站

LED 表示的是：

> **物理位置**

不是：

> **這班車會不會停該站**

例如直達車：

```text
A1 → A3
```

雖然不一定停 A2，但實際列車仍會經過 A2 附近。

所以 LED 仍可能：

```text
A1 → A2 → A3
```

依物理位置亮過 A2。

這是正常設計。

---

# 19. 常見故障

## A1～A8 全部不亮，A9 正常

優先檢查：

```text
74HC595 VCC
74HC595 GND
OE 是否 GND
SRCLR 是否 3.3V
DATA / CLOCK / LATCH
IC 方向
```

因為 A9 不經過 74HC595。

---

## 只有某一站不亮

例如只有 A4 不亮：

檢查：

1. LED 是否反向。
2. LED 是否損壞。
3. 330 Ω 是否接好。
4. QD → A4 wire。
5. 該 Breadboard row 是否插錯。
6. ESPHome switch mapping。

---

## Chase 順序錯

例如：

```text
A1
A3
A2
A4
```

通常是：

- QA/QB/QC output 線接錯
- IC pin 判斷錯
- ESPHome `number` mapping 錯

---

## 全部燈異常閃爍

檢查：

- GND 是否共地
- 3.3 V 是否穩定
- DATA/CLOCK/LATCH 是否鬆動
- Breadboard jumper 是否接觸不良

若未來做永久版本，建議在 74HC595 VCC / GND 附近加 0.1 µF 去耦。

---

## A9 行為與 A1～A8 不一致

A9 是獨立：

```text
GPIO16
```

所以檢查：

```text
D0 / GPIO16 wire
A9 LED 極性
A9 resistor
ESPHome GPIO16 switch
```

---

# 20. 為什麼目前供電可行？

目前只是：

- 9 顆一般 LED
- 74HC595
- ESP8266 logic

而且 LED 有 330 Ω 限流。

這個小型 prototype 已實際正常運作。

但若未來擴充：

- 更多 LED
- 高亮 LED
- RGB LED
- 多顆 Shift Register
- 額外顯示器

就不應直接假設 NodeMCU 3.3 V rail 一定適合，需重新做電流預算與電源設計。

---

# 21. 未來轉成洞洞板 / PCB

若要永久化，建議：

1. 保留相同 GPIO mapping。
2. 74HC595 附近加 0.1 µF 去耦。
3. 明確標示 A1～A9。
4. 每顆 LED 保留獨立 resistor。
5. 保留測試點：
   - 3V3
   - GND
   - DATA
   - CLOCK
   - LATCH
6. 若擴充 A10～A22，考慮串接更多 74HC595。

---

# 22. V1 硬體完成狀態

目前已實際驗證：

```text
NodeMCU                   ✅
SN74HC595                 ✅
A1～A8 shift outputs      ✅
A9 GPIO16                 ✅
9 × 330Ω                  ✅
All On                    ✅
All Off                   ✅
Chase                     ✅
HA Frame A/B              ✅
600ms Renderer            ✅
多車                      ✅
站間動畫                  ✅
```

所以若目標只是：

> **A1～A9 一排實體列車位置顯示器**

目前 V1 硬體可以視為完工。
