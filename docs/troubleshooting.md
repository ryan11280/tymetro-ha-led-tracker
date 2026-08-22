# 故障排除

建議依資料流由上到下排查：

```text
TDX
↓
HA Static / Live
↓
Tracker
↓
Frame
↓
ESPHome
↓
SN74HC595 / GPIO
↓
LED
```

不要一看到 LED 不對就直接改 Python。

---

# 1. `sensor.tymetro_static_model_raw = error`

檢查 Attribute：

```text
s2s_http
stopping_pattern_http
timetable_a1_http
timetable_a8_http
```

只要其中一個不是 200，就先處理 TDX / OAuth / URL / Network。

---

# 2. `sensor.tdx_token` 沒有 access_token

檢查：

```text
secrets.yaml
tdx_auth_payload
```

格式：

```text
grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET
```

不要把真實 credential 貼到 Issue 或 GitHub。

---

# 3. Tracker `unavailable`

通常代表：

```text
Static Model 還沒 ready
```

先看：

```text
sensor.tymetro_static_model_raw
```

---

# 4. Tracker 有 train，但 LED 不動

先看：

```text
sensor.tymetro_led_frame_a
sensor.tymetro_led_frame_b
```

如果有正常數字變化：

```text
問題比較靠近 ESPHome / hardware
```

如果一直不存在：

```text
問題在 Tracker / HA
```

---

# 5. Frame A/B 正常，但 ESPHome 沒反應

檢查：

- ESPHome Device online
- Native API connected
- `sensor.tymetro_led_frame_a`
- `sensor.tymetro_led_frame_b`
- ESPHome log
- API encryption key 是否一致

---

# 6. A1～A8 全壞、A9 正常

高度懷疑 74HC595 路徑：

```text
VCC
GND
OE
SRCLR
DATA
CLOCK
LATCH
IC 方向
```

因為 A9 完全不經 74HC595。

---

# 7. A9 壞、A1～A8 正常

檢查：

```text
D0 / GPIO16
A9 jumper
LED polarity
330Ω
```

---

# 8. 只有某一顆壞

檢查：

- LED
- LED 是否反插
- resistor
- jumper
- 74HC595 對應 output
- Breadboard row
- ESPHome number mapping

---

# 9. Chase 順序錯

表示：

```text
Output mapping
```

而不是時刻表。

檢查 QA～QH 與 A1～A8 的實體 wire。

---

# 10. LED 測試一按就被 Tracker 搶回去

目前設定應該不會立即發生。

Test Button 會先：

```text
tymetro_renderer_paused = true
```

測完再恢復。

如果你自行改過 ESPHome YAML，要確認 pause 邏輯仍存在。

---

# 11. Live Mode 顯示 `schedule_live_stale`

這不一定是你的設定錯。

先看：

```text
live_source_age_seconds
live_source_update
```

如果 source age 很大：

```text
TDX / TYMC 上游資料真的過期
```

HTTP 200 也一樣可能 stale。

---

# 12. Live Mode 一直 `schedule_live_pending`

表示：

```text
Live Mode ON
Live source 不一定 stale
但還沒有可信 matching
```

需要檢查：

```text
live_match_count
live_matched_event_count
corrected_train_count
```

不應為了「一定要顯示 Live」而隨便放寬 matching。

---

# 13. Dashboard 出現 `Custom element doesn't exist`

通常是 JS Resource 沒載入。

檢查：

```text
/homeassistant/www/tymetro-tracker-card.js
```

Resource：

```text
/local/tymetro-tracker-card.js?v=2
```

Type：

```text
JavaScript Module
```

然後：

```text
Ctrl + F5
```

---

# 14. 更新 JS 但畫面沒變

瀏覽器 cache。

把：

```text
?v=2
```

改成：

```text
?v=3
```

只是 cache busting，不代表一定要修改 card internal version。

---

# 15. Dashboard marker 與 LED 看起來不同

有可能是正常。

Dashboard：

```text
連續位置
```

LED：

```text
離散站點 + Frame A/B 動畫
```

兩者的視覺 encoding 不一樣，但底層 train model 是同一個。

---

# 16. 直達車在 A2 附近亮

正常。

LED 表示物理位置，不表示停靠資格。

---

# 17. HA 重啟後短時間沒有列車

Static Model 會：

```text
HA startup
→ delay
→ update token
→ fetch Static APIs
→ ready
```

所以重啟後不一定瞬間就有 Tracker data。

---

# 18. HA 冷啟動時 TDX 掛掉

目前 V1 沒有 persistent Static cache。

因此可能無法建立 Schedule。

這是已知限制，不是未知 bug。

請看：

[reliability.md](reliability.md)

---

# 19. Python Script 修改後沒生效

Home Assistant `python_script` 通常需要 Reload / Restart 才會重新讀檔。

最穩妥：

```text
修改 script
→ Check config
→ Restart HA
```

---

# 20. ESPHome YAML 修改後沒生效

ESP8266 端必須重新：

```text
Install / OTA
```

修改 HA 檔案不會自動改 ESP8266 firmware。
