# 系統架構

本文件說明 TYMetro HA LED Tracker 的整體資料流、模組責任與設計取捨。

---

# 設計目標

1. ESP8266 的工作越單純越好。
2. TDX OAuth、JSON、時刻表與 matching 留在 Home Assistant。
3. 正常 Schedule 使用不要大量消耗 TDX API。
4. Live 資料不可信時，寧可退回 Schedule，也不要顯示假的 realtime。
5. Dashboard 與實體 LED 使用同一份列車模型。
6. 快速 LED 動畫在 ESP8266 本地處理，不讓 HA 每 600 ms 發一次狀態。

---

# 整體資料流

```mermaid
flowchart TD
    subgraph TDX
      AUTH[OAuth Token]
      S2S[S2STravelTime]
      STOP[StoppingPattern]
      A1[StationTimeTable A1]
      A8[StationTimeTable A8]
      LIVE[LiveBoard TYMC]
    end

    AUTH --> TOKEN[sensor.tdx_token]

    S2S --> STATIC
    STOP --> STATIC
    A1 --> STATIC
    A8 --> STATIC

    LIVE --> RAWLIVE

    subgraph Home_Assistant[Home Assistant]
      TOKEN
      STATIC[sensor.tymetro_static_model_raw]
      RAWLIVE[sensor.tymetro_liveboard_raw]
      DIR[input_select.tymetro_direction]
      MODE[input_boolean.tymetro_live_mode]
      CORE[python_script.tymetro_tracker]
      TRACK[sensor.tymetro_tracker]
      F1[sensor.tymetro_led_frame_a]
      F2[sensor.tymetro_led_frame_b]
    end

    STATIC --> CORE
    RAWLIVE --> CORE
    DIR --> CORE
    MODE --> CORE

    CORE --> TRACK
    CORE --> F1
    CORE --> F2

    TRACK --> DASH[Animated Lovelace Card]
    F1 --> ESP
    F2 --> ESP

    subgraph ESPHome
      ESP[NodeMCU v2]
      RENDER[600 ms Frame Renderer]
      HC[SN74HC595]
      GPIO[GPIO16]
    end

    ESP --> RENDER
    RENDER --> HC
    RENDER --> GPIO

    HC --> A18[A1～A8 LED]
    GPIO --> A9LED[A9 LED]
```

---

# 靜態資料模型（Static Model）

靜態資料會在：

```text
Home Assistant 啟動
每天 03:30
```

重新抓取。

使用四個 Metro API：

- `S2STravelTime/TYMC`
- `StoppingPattern/TYMC`
- `StationTimeTable/TYMC`，A1
- `StationTimeTable/TYMC`，A8

最後組成：

```text
sensor.tymetro_static_model_raw
```

## 為什麼用 A1 和 A8 當時刻表 Anchor？

### A1

A1 是顯示區間的台北端端點，適合用來建立往 A9 方向列車進入 A1～A9 的時間軸。

### A8

往 A1 方向的列車需要一個可靠 anchor，而 A8 同時是普通車與直達車的重要停靠站，所以適合拿來建立北上 trajectory。

---

# Tracker 核心

核心程式：

```text
home-assistant/python_scripts/tymetro_tracker.py
```

由：

```text
TYMetro - Tracker Engine
```

每 5 秒呼叫一次。

程式主要工作：

1. 判斷目前 Service Day。
2. 處理跨午夜營運日。
3. 從 TDX S2S 建立站間 runtime。
4. 建立普通車 trajectory。
5. 建立直達車 trajectory。
6. 補出直達車通過不停靠站的實體位置。
7. 找出目前 A1～A9 範圍內的列車。
8. 判斷列車：
   - 在站內
   - 在兩站之間
9. 計算 `progress`。
10. 建立 canonical train list。
11. 產生 Frame A / Frame B。

---

# 核心 Tracker Entity

主要 UI / Data Entity：

```text
sensor.tymetro_tracker
```

重要 Attribute：

```yaml
direction: to_a1 | to_a9
direction_label: "← 往 A1 台北" | "往 A9 林口 →"

mode:
  schedule
  schedule_live_pending
  live
  schedule_live_stale

live_requested: true | false
live_correction_active: true | false

live_source_update: ISO8601
live_source_age_seconds: integer

live_match_count: integer
live_matched_event_count: integer
corrected_train_count: integer

service_day: Monday ... Sunday
updated_at: ISO8601

train_count: integer

frame_a: 0..511
frame_b: 0..511

trains: [...]
```

典型 Train Object：

```yaml
key: "N|22:24|A1|1|SP1"
type: local
train_type: 1
pattern: SP1
destination: A1

state: between

station: ""
from: A6
to: A5
progress: 0.889

anchor: "22:28"

live_corrected: false
delay_seconds: 0
delay_minutes: 0
```

---

# 時刻表列車軌跡

## 普通車

普通車停靠 A1～A9 全站，因此可直接按照官方 S2S runtime 建立：

```text
A1 → A2 → A3 → A4 → ... → A9
```

## 直達車

直達車在 A1～A9 不是每站停。

但實體列車即使不停 A2，仍然會實際經過 A2 的空間位置。

因此 Tracker 不能直接：

```text
A1 → A3
```

瞬移。

而是用普通車的實體站間比例，把 A1→A3 的 Express runtime 分配到：

```text
A1 → A2 → A3
```

所以 LED / Dashboard 仍能呈現列車「通過 A2 附近」，只是 Train Type / Stopping Pattern 仍然知道它不在 A2 停車。

---

# 到站 / 站間狀態

## 到站

例如列車停在 A5：

```yaml
state: station
station: A5
```

LED：

```text
Frame A = A5
Frame B = A5
```

## 站間

例如：

```yaml
state: between
from: A5
to: A6
progress: 0.58
```

代表列車已完成 A5→A6 約 58%。

Dashboard 可以直接畫：

```text
A5 + 58% × (A6 - A5)
```

---

# LED Frame 模型

Frame 為 9-bit integer：

```text
A1 A2 A3 A4 A5 A6 A7 A8 A9
b0 b1 b2 b3 b4 b5 b6 b7 b8
```

例如：

```text
A1             = 1
A1+A3+A5+A8    = 149
全部 A1～A9    = 511
```

站內：

```text
Frame A：A5 ON
Frame B：A5 ON
```

站間中段：

```text
Frame A：A5 ON
Frame B：A6 ON
```

ESP8266 每 600 ms 切換兩個 frame。

---

# 為什麼 Direction 由使用者選？

目前實體原型只有：

```text
一排 A1～A9 LED
```

如果同時顯示：

```text
往 A1
+
往 A9
```

使用者無法單靠同一顆 LED 判斷某班車是哪個方向。

因此 V1 使用：

```text
input_select.tymetro_direction
```

切換：

```text
← 往 A1 台北
往 A9 林口 →
```

Dashboard 未來可以不受這個硬體限制，做雙向同時顯示。

---

# LiveBoard 不是 GPS

這是整個 Live 架構最重要的前提。

TDX LiveBoard 是「車站 ETA」資料，並不是：

```text
Train GPS Position Feed
```

它提供的資訊比較像：

```text
A8
往 A1
預估 10 分鐘
預估 25 分鐘
預估 41 分鐘
...
```

而不是：

```text
Train 1234
Lat / Lon
目前位於 A6.42
```

所以 Live Mode 的正確做法是：

```text
Schedule trajectory
      +
Live station ETA events
      ↓
Matching
      ↓
Delay correction
```

而不是拿 LiveBoard 當 GPS。

---

# 即時資料 Matching 流程

1. Tracker 先建立近期 Schedule train candidates。
2. 把 LiveBoard ETA 轉成預估實際到站時間。
3. 比對：
   - 車站
   - 方向
   - Destination
   - 時間窗口
4. 找可信的 scheduled event。
5. 算出：
   ```text
   Live ETA - Schedule ETA
   ```
6. 對同一列車多個 matched event 取穩健 correction。
7. 把 correction 套回整條 schedule timeline。

若：

- 資料過期
- matching 不唯一
- 時間差太離譜

則不校正。

---

# 即時資料新鮮度判斷

目前 Tracker 使用：

```text
SrcUpdateTime
```

判斷 Live source 新鮮度。

門檻：

```text
300 秒
```

超過後：

```text
mode = schedule_live_stale
live_correction_active = false
```

並繼續 Schedule。

---

# ESPHome 的責任邊界

ESP8266 完全不需要理解：

- TDX
- TrainType
- StoppingPattern
- ServiceDay
- ETA
- Schedule
- Live
- Destination

它只需要兩個數字：

```text
Frame A：0～511
Frame B：0～511
```

這種切法的好處是：

- ESPHome 設定簡單
- 硬體不依賴 TDX 格式
- HA 演算法改版不需要重寫硬體
- LED renderer 可以保持穩定
- Dashboard 與硬體都能吃同一份 Tracker Core

---

# 可靠性邊界

只要 Static Model 已載入：

```text
列車位置 = Home Assistant 本機運算
```

LiveBoard 完全是 optional。

目前 V1 尚未做到：

```text
HA 冷啟動
+
TDX Static API 全掛
+
仍自動從 persistent cache 恢復
```

這是後續可靠性強化項目。

請看：

[reliability.md](reliability.md)
