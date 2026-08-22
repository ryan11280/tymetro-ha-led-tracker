# 安裝流程

這份文件假設你已經有一套正常運作的 Home Assistant 與 ESPHome。

---

# 1. 硬體

先依：

[hardware.md](hardware.md)

完成：

```text
NodeMCU
SN74HC595
9 × LED
9 × 330Ω
```

先不要急著接 TDX。

第一階段只要做到：

```text
All LEDs On
All LEDs Off
Chase Test
```

都正常即可。

---

# 2. 建立 ESPHome 裝置

使用：

```text
esphome/tymetro-led.yaml
```

真正的 secret 放在 ESPHome private secrets。

可參考：

```text
esphome/secrets.example.yaml
```

至少需要：

```yaml
wifi_ssid:
wifi_password:
tymetro_api_encryption_key:
tymetro_fallback_password:
```

不要直接把真實值寫進公開 repo 版本。

---

# 3. 寫入 ESPHome 韌體

第一次可 USB flash。

之後可 OTA。

完成後確認：

- Device online
- HA 發現 ESPHome Device
- A1～A9 switch 存在
- 三個 test button 存在

---

# 4. 建立 Home Assistant Helpers

請看：

```text
home-assistant/helpers.md
```

需要：

```text
input_select.tymetro_direction
input_boolean.tymetro_live_mode
timer.tymetro_live_session
```

Direction Options 必須完全一致：

```text
← 往 A1 台北
往 A9 林口 →
```

---

# 5. 啟用 Python Script 整合

`configuration.yaml` 必須包含：

```yaml
python_script:
```

如果本來已有：

```yaml
python_script:
```

不要重複建立第二個同名 top-level key。

---

# 6. 放入 Tracker Script

把：

```text
home-assistant/python_scripts/tymetro_tracker.py
```

放到：

```text
/homeassistant/python_scripts/tymetro_tracker.py
```

---

# 7. 設定 TDX 憑證

到 Home Assistant：

```text
/homeassistant/secrets.yaml
```

加入：

```yaml
tdx_auth_payload: 'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET'
```

將 placeholder 換成你自己的 TDX credential。

**不要上傳 secrets.yaml 到 Git。**

---

# 8. 合併 configuration-snippet.yaml

開：

```text
home-assistant/configuration-snippet.yaml
```

合併到你的：

```text
/homeassistant/configuration.yaml
```

特別注意：

```yaml
python_script:
recorder:
rest:
rest_command:
template:
```

Home Assistant 同一個 top-level key 不能隨便重複。

如果你原本就有：

```yaml
recorder:
```

要把 `exclude.entities` 合併進去。

不是再貼第二個：

```yaml
recorder:
```

---

# 9. 檢查 Home Assistant 設定

在 Restart 前先跑：

```text
Check configuration
```

確定 YAML 正常。

---

# 10. 重新啟動 Home Assistant

重新啟動後先確認：

```text
sensor.tdx_token
```

存在。

接著等待 Static Model。

---

# 11. 確認靜態資料模型

確認：

```text
sensor.tymetro_static_model_raw
```

State：

```text
ready
```

Attribute：

```text
s2s_http = 200
stopping_pattern_http = 200
timetable_a1_http = 200
timetable_a8_http = 200
```

如果不是 `ready`，先不要除錯 ESPHome，因為 Tracker Core 還沒有資料。

---

# 12. 加入 Automations

加入：

```text
home-assistant/automations/live-session-control.yaml
home-assistant/automations/tracker-engine.yaml
home-assistant/automations/abort-stale-live.yaml
```

可以用 HA UI 建立 YAML Automation，再貼內容。

---

# 13. 啟用 Tracker Engine

確認：

```text
TYMetro - Tracker Engine
```

已 Enabled。

它會在：

```text
每 5 秒
Direction 改變
Live Mode 改變
Static Model fetched_at 改變
LiveBoard fetched_at 改變
```

執行：

```text
python_script.tymetro_tracker
```

---

# 14. 確認 Tracker Entity

找到：

```text
sensor.tymetro_tracker
```

正常應看到：

```text
state = schedule
```

或：

```text
schedule_live_pending
schedule_live_stale
live
```

並有：

```text
trains
frame_a
frame_b
```

---

# 15. 確認 LED Frame

應出現：

```text
sensor.tymetro_led_frame_a
sensor.tymetro_led_frame_b
```

值：

```text
0～511
```

---

# 16. ESPHome 接收 Frame

ESPHome Device log 應該能看到 HA API connection。

然後：

```text
tymetro_frame_a
tymetro_frame_b
```

會取得 HA sensor state。

ESPHome 每 600 ms 在本機 renderer。

---

# 17. 安裝 Dashboard 自訂卡片

將：

```text
dashboard/tymetro-tracker-card.js
```

放到：

```text
/homeassistant/www/tymetro-tracker-card.js
```

---

# 18. 加入 Dashboard 資源

在 Home Assistant Dashboard Resource 新增：

```text
/local/tymetro-tracker-card.js?v=2
```

類型：

```text
JavaScript Module
```

如果第一次建立 `/homeassistant/www/` 後 `/local/...` 404，可 Restart HA 一次。

瀏覽器更新：

```text
Ctrl + F5
```

---

# 19. 加入「機捷」頁面

使用：

```text
dashboard/view.yaml
```

加入既有 Dashboard 的：

```yaml
views:
```

---

# 20. 時刻表模式驗收

保持：

```text
Live Mode OFF
```

確認：

1. Tracker state = `schedule`
2. train_count 合理
3. Dashboard marker 移動
4. Frame A/B 變動
5. 實體 LED 變動
6. 切換 A1 / A9 方向有反應

---

# 21. 即時模式驗收

開啟：

```text
TDX 即時模式
```

預期：

```text
Timer = 15:00
LiveBoard 開始每 30 秒取得
```

若 TDX source 新鮮：

```text
schedule_live_pending
→ live
```

若 source 太舊：

```text
schedule_live_stale
```

Schedule 繼續。

---

# 22. 驗收文件

完整測試流程：

[verification.md](verification.md)

故障排除：

[troubleshooting.md](troubleshooting.md)

TDX 資料：

[tdx-data.md](tdx-data.md)
