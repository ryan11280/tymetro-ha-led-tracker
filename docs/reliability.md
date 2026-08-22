# 可靠性與故障模式

本專案把 Schedule Mode 當成主要運作模式，Live Mode 當成 optional correction layer。

---

# 1. 正常 Schedule Mode

只要 Static Model 已經成功載入：

```text
TDX Static Data
      ↓
Home Assistant 已保存 Entity State
      ↓
每 5 秒本機計算列車位置
```

因此列車每 5 秒移動並不需要每次連外。

---

# 2. LiveBoard 掛掉

不影響 Schedule。

```text
LiveBoard unavailable / stale
      ↓
live_correction_active = false
      ↓
Schedule trajectory 繼續
```

這是預期行為。

---

# 3. LiveBoard HTTP 200 但內容過期

這種情況已實際遇過。

因此系統不能只判斷：

```text
HTTP == 200
```

而必須看：

```text
SrcUpdateTime
```

目前大於：

```text
300 秒
```

就視為 stale。

---

# 4. TDX OAuth 短暫失敗

Static / Live request 需要 Bearer Token。

設定在必要時會要求 HA 更新：

```text
sensor.tdx_token
```

並等待 token 出現。

如果無法取得 token，對應的 TDX fetch 不會有有效資料。

---

# 5. Home Assistant 重啟

目前：

- Live Mode 在 HA startup 時被強制 OFF。
- Live timer 被取消。
- Static Model 會重新抓取。
- Tracker 在 Static Model ready 後繼續。

這可以避免重啟後意外繼續消耗 Live API 額度。

---

# 6. Cold Start + TDX Static API 全掛

這是目前 V1 最明確的可靠性缺口。

如果：

```text
HA 剛啟動
+
sensor.tymetro_static_model_raw 尚未建立有效內容
+
TDX Static API 無法連線
```

Tracker 無法從空資料建立時刻表 trajectory。

## 未來改善

可加入：

```text
persistent local static cache
```

例如：

1. 每次 Static Model 成功時保存 JSON 到本地。
2. 啟動時先使用最後成功版本。
3. TDX 可用時再刷新。
4. 資料 cache 標示 timestamp。

這樣能把系統變成：

```text
TDX 完全斷線
+
HA 重啟
↓
仍可用上次成功時刻表模擬
```

目前尚未實作。

---

# 7. ESP8266 / HA 暫時斷線

ESPHome Frame sensor 來自 Home Assistant。

如果 API 中斷：

- ESP8266 不會取得新的 frame。
- renderer 不會有新的列車模型。

V1 尚未加入：

```text
Frame age watchdog → 自動全滅
```

若未來希望更嚴格 fail-safe，可加入「超過 N 秒未收到 HA frame 就熄燈」。

目前家庭 LAN / HA 環境使用下不是必要項。

---

# 8. 74HC595 故障

A1～A8 共用同一顆 IC。

因此若 74HC595：

- 掉電
- OE 錯誤
- DATA/CLOCK/LATCH 斷線

可能造成：

```text
A1～A8 一起失效
```

而 A9 仍可能正常，因為 A9 使用獨立 GPIO16。

這也是很好的診斷線索。

---

# 9. 單顆 LED 故障

如果只一站壞：

```text
A4 不亮
其他正常
```

較可能是：

- LED
- resistor
- jumper
- 74HC595 對應 output

而不是 HA Tracker Core。

---

# 10. Live Mode 額度保護

Live Mode：

```text
手動 ON
→ 最多 15 分鐘
→ 每 30 秒 request
```

而非：

```text
24/7 polling
```

目的：

- 控制免費 TDX quota
- Live 只是需要時才使用
- Schedule 本身已經足夠當日常模式

---

# 11. Stale Auto Abort

Automation：

```text
TYMetro - Abort Stale Live
```

Live Mode 打開後等待 40 秒。

如果 Tracker 仍：

```text
schedule_live_stale
```

就：

```text
Live Mode OFF
+
建立 HA Persistent Notification
```

避免一直浪費 request。

目前 Automation 已建立；仍建議做一次完整 40 秒實際驗收。

---

# 12. V1 可靠性結論

目前可以合理聲稱：

> 正常網路環境中，Schedule Tracker 可以自行長期運作；TDX LiveBoard 故障不會讓主系統停擺。

目前不能聲稱：

> 即使 HA 冷啟動當下 TDX Static API 完全不可用，也一定能離線恢復。

要達成後者，需要 static persistent cache。
