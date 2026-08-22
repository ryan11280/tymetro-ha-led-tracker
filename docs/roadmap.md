# 開發路線圖

Roadmap 以「是否值得增加實際功能」為原則，不追求為了持續開發而開發。

---

# v0.1 — V1 時刻表 Tracker

狀態：

```text
✅ 完成
```

包含：

- A1～A9
- 普通 / 直達
- Schedule trajectory
- 5 秒 Tracker Engine
- Frame A/B
- NodeMCU
- SN74HC595
- 9 LED
- 600 ms renderer
- Direction
- Animated Dashboard
- LiveBoard ingestion
- stale fallback

---

# v0.2 — 即時資料驗證

優先：

```text
🟡 待 TDX TYMC 上游恢復新鮮資料
```

目標：

- 驗證 Fresh LiveBoard
- 驗證 schedule-to-live matching
- 驗證 delay correction
- 驗證 `mode = live`
- 驗證 `live_correction_active`
- 驗證 Dashboard / LED 校正後結果
- 驗證 40 秒 stale auto-abort

---

# v0.3 — 可靠性強化

視需求實作：

- Static Model persistent cache
- HA cold start offline fallback
- Static cache timestamp
- Frame age watchdog
- TDX health metadata
- 更完整 error state

---

# v0.4 — 實體裝置永久化

若希望從 Breadboard 變永久裝置：

- 洞洞板 / PCB
- 0.1 µF decoupling
- 外殼
- 印刷 A1～A9 station label
- USB-C / 更穩定供電
- Wall mount / Desk display

---

# v0.5 — 路線擴充

可選：

- A1～A22
- 串接第二 / 第三顆 74HC595
- Dashboard 全線
- 依 viewport 顯示局部線段

---

# 未來構想

不承諾實作：

- 雙方向同時 LED
- 雙排 LED
- OLED 狀態資訊
- RGB train type
- 實體按鍵方向切換
- Web configuration
- MQTT alternative
- Train detail interaction
- 目的地 / delay 詳細顯示

---

# 目前原則

V1 UI / 硬體已足夠使用。

下一個真正有價值的工程里程碑是：

> **TDX LiveBoard realtime matching 實際驗證成功。**

除非有新需求，不建議繼續無限美化目前 UI 或 Breadboard。
