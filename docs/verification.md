# 驗收紀錄與測試流程

本文件區分：

- 已實際驗證
- 已設定但待驗收
- 尚未完成

避免 README 把「寫好程式」當成「實際驗證成功」。

---

# 1. 硬體基本測試

## All LEDs Off

操作：

```text
ESPHome → All LEDs Off
```

預期：

```text
A1～A9 全暗
```

狀態：

```text
✅ 已驗證
```

---

## All LEDs On

操作：

```text
ESPHome → All LEDs On
```

預期：

```text
A1～A9 全亮
```

狀態：

```text
✅ 已驗證
```

---

## Chase

預期：

```text
A1 → A2 → ... → A9 → A8 → ... → A1
```

狀態：

```text
✅ 已驗證
```

---

# 2. Home Assistant → ESPHome

確認 ESPHome API 成功連到 HA。

Frame sensor：

```text
sensor.tymetro_led_frame_a
sensor.tymetro_led_frame_b
```

狀態：

```text
✅ 已驗證
```

曾在 log 中實際看到：

- A8 / A9 交替
- 同時另一組 A4 / A5 交替

代表多組站間動畫可同時 render。

---

# 3. Static Model

確認：

```text
sensor.tymetro_static_model_raw
```

State：

```text
ready
```

並確認：

```text
s2s_http = 200
stopping_pattern_http = 200
timetable_a1_http = 200
timetable_a8_http = 200
```

狀態：

```text
✅ 已驗證
```

---

# 4. Tracker

確認：

```text
sensor.tymetro_tracker
```

有：

```text
direction
mode
service_day
train_count
frame_a
frame_b
trains
```

狀態：

```text
✅ 已驗證
```

實際曾出現多班列車，例如：

- 普通車在 A1
- 直達車 A3→A2
- 普通車 A6→A5
- 直達車 A8
- 普通車 A8

代表 Schedule Model 能同時建立多班 trajectory。

---

# 5. Frame

確認：

```text
frame_a
frame_b
```

都在：

```text
0～511
```

狀態：

```text
✅ 已驗證
```

---

# 6. Direction

Dashboard 切：

```text
← 往 A1 台北
```

確認：

- `input_select.tymetro_direction`
- Tracker direction
- Train list
- LED

一起更新。

再切：

```text
往 A9 林口 →
```

重複確認。

狀態：

```text
✅ 已驗證
```

---

# 7. Dashboard

確認：

- A1～A9 一排
- Marker 位置符合 `from / to / progress`
- 多班車可同時顯示
- 5 秒 update 間平滑移動
- 普通 / 直達顯示
- Train progress list
- Direction control

狀態：

```text
✅ 已驗證
```

---

# 8. LiveBoard API

開 Live Mode。

確認：

```text
sensor.tymetro_liveboard_raw
```

包含：

```text
http_status
fetched_at
records
```

狀態：

```text
✅ API ingestion 已驗證
```

---

# 9. LiveBoard Stale Test

實際測到：

```text
HA fetched_at：
約 22:43

newest SrcUpdateTime：
約 21:47

newest UpdateTime：
約 21:50

HTTP：
200

records：
96
```

代表：

```text
網路正常
API endpoint 正常
但 TYMC source data 過期
```

Tracker：

```text
mode = schedule_live_stale
live_correction_active = false
corrected_train_count = 0
```

狀態：

```text
✅ 已驗證
```

---

# 10. Live Matching

需要 TDX TYMC 回傳足夠新鮮資料。

理想驗收：

```text
Live Mode ON
↓
live_source_age_seconds < 300
↓
Live events match schedule candidates
↓
live_match_count > 0
↓
corrected_train_count > 0
↓
live_correction_active = true
↓
mode = live
```

狀態：

```text
🟡 待實測
```

原因：

```text
最新一次測試時 TYMC 上游資料 stale
```

---

# 11. Stale Auto Abort

測試：

1. Live Mode ON。
2. 確認 Tracker 為 `schedule_live_stale`。
3. 不手動關閉。
4. 等待 40 秒。
5. 確認：
   ```text
   input_boolean.tymetro_live_mode = off
   ```
6. 確認出現 Persistent Notification。

狀態：

```text
🟡 Automation 已建立，建議補最後一次完整驗收
```

---

# 12. HA Restart

建議驗收：

1. Live Mode OFF。
2. Restart Home Assistant。
3. 確認 Live Mode 仍 OFF。
4. 確認 Live Timer cancel。
5. 等 Static Model ready。
6. 確認 Tracker 自動恢復。
7. 確認 Dashboard / LED 自動恢復。

核心 Schedule startup：

```text
✅ 已能正常建立
```

若要做到 TDX Static API 全掛仍恢復，需未來 local cache。

---

# 13. V1 Acceptance

## 已通過

```text
Hardware wiring                 ✅
All On / Off                    ✅
Chase                           ✅
ESPHome API                     ✅
HA Frame subscription           ✅
600ms renderer                  ✅
Static TDX ingestion            ✅
Schedule trajectory             ✅
Local / Express                 ✅
Multi-train                     ✅
Direction                       ✅
Animated dashboard              ✅
LiveBoard ingestion             ✅
Stale rejection                 ✅
Schedule fallback               ✅
```

## 尚未最後通過

```text
Fresh Live matching             🟡
Realtime delay correction       🟡
40s stale auto-off              🟡
Offline static cold-start       ⬜
```
