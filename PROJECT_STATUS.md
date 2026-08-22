# 專案進度

最後更新：**2026-08-22**

## 總結

目前 **V1 Schedule Tracker 已可視為功能完成**。

主流程已經完整運作：

```text
TDX 官方靜態資料
      ↓
Home Assistant Static Model
      ↓
python_script.tymetro_tracker
每 5 秒本機運算
      ↓
列車物件 + Frame A / Frame B
      ├──────────→ Home Assistant 動態 Dashboard
      └──────────→ ESPHome 600 ms renderer
                         ↓
                   A1～A9 實體 LED
```

目前剩餘工作主要集中在 TDX LiveBoard 上游資料恢復後的即時校正實測，以及未來可選的可靠性強化。

---

# 1. 實體硬體 / ESPHome

## 已驗證

- [x] NodeMCU v2 / ESP8266 正常連線 ESPHome
- [x] NodeMCU USB 供電
- [x] Breadboard 使用 NodeMCU `3V3` / `GND`
- [x] 最終原型不使用 MB102
- [x] SN74HC595 控制 A1～A8
- [x] `D0 / GPIO16` 控制 A9
- [x] 九顆 LED 各自使用 330 Ω
- [x] A1～A9 個別 output 正常
- [x] All LEDs On
- [x] All LEDs Off
- [x] A1 → A9 → A1 Chase Test
- [x] 測試期間 renderer 會暫停
- [x] 測試完成後 renderer 會恢復
- [x] ESPHome 正確訂閱 HA Frame A / Frame B
- [x] 600 ms frame alternation
- [x] 到站穩定亮
- [x] 站間相鄰 LED 動畫
- [x] 多班列車可同時合併顯示
- [x] 實際觀察到多組站間動畫同時運作

## 非必要、尚未實作

- [ ] 焊接洞洞板
- [ ] PCB
- [ ] 外殼
- [ ] 0.1 µF 74HC595 本地去耦電容
- [ ] A10～A22
- [ ] 雙方向雙排 LED

上述項目都不是目前 V1 正常運作所必需。

---

# 2. Home Assistant Schedule Engine

## 已完成

- [x] Direction helper
- [x] Live Mode helper
- [x] 15 分鐘 Live Session Timer
- [x] TDX OAuth Client Credentials
- [x] `S2STravelTime`
- [x] `StoppingPattern`
- [x] A1 `StationTimeTable`
- [x] A8 `StationTimeTable`
- [x] Service Day 判斷
- [x] 午夜跨日營運日處理
- [x] 普通車 trajectory
- [x] 直達車 trajectory
- [x] 直達車跳站區間的物理位置插值
- [x] A9 → A8 北上 pre-anchor 處理
- [x] Station state
- [x] Between-station state
- [x] `progress = 0.0～1.0`
- [x] 多車 train list
- [x] Frame A
- [x] Frame B
- [x] 9-bit mask
- [x] 每 5 秒本機重新計算
- [x] 切換方向立即重新計算
- [x] Static Model 更新後立即重新計算
- [x] LiveBoard 更新後立即重新計算

---

# 3. Home Assistant UI

## 已完成

- [x] 專用「機捷」View
- [x] A1～A9 單線軌道
- [x] 桌面一次完整顯示 A1～A9
- [x] 手機 responsive
- [x] 普通 / 直達 marker
- [x] 依 `from / to / progress` 呈現真正站間位置
- [x] 每 5 秒資料間以前端 transition 平滑移動
- [x] 多列車靠近時自動上下錯位
- [x] 列車淡入 / 淡出
- [x] 方向切換
- [x] Live Mode 開關
- [x] Schedule / Live / Stale Badge
- [x] 目前列車清單
- [x] Progress bar
- [x] Debug / system state 顯示

目前 UI 已暫時封版，不再進行純美化調整。

---

# 4. TDX LiveBoard

## 已完成

- [x] Live Mode 開啟時立即抓 LiveBoard
- [x] 開啟期間每 30 秒 polling
- [x] Live Mode 關閉時不 polling
- [x] 只保存 A1～A9 records
- [x] HTTP 狀態記錄
- [x] `fetched_at`
- [x] 解析 `SrcUpdateTime`
- [x] 解析 `UpdateTime`
- [x] 300 秒新鮮度門檻
- [x] stale → `schedule_live_stale`
- [x] stale 時不假裝資料為 realtime
- [x] Schedule fallback
- [x] 40 秒 stale abort automation 已建立
- [x] persistent notification 已建立

## 待最後實測

- [ ] Fresh TYMC LiveBoard feed
- [ ] schedule candidate ↔ Live ETA matching
- [ ] matched event count
- [ ] train delay median correction
- [ ] `live_correction_active = true`
- [ ] `mode = live`
- [ ] 修正後 Dashboard / LED 與實際列車情況合理一致
- [ ] 40 秒 stale abort 實際等待驗收

---

# 5. 已驗證的故障保護

曾實際遇到：

```text
HA 取得 LiveBoard 的時間：22:43 左右
TDX SrcUpdateTime：約 21:47
TDX UpdateTime：約 21:50
HTTP：200
```

也就是 API 本身可連線，但桃捷上游資料已經過期約一小時。

Tracker 正確判斷為：

```text
schedule_live_stale
```

並且：

```text
live_correction_active = false
corrected_train_count = 0
```

仍繼續使用 Schedule 模型。

這代表：

> `HTTP 200` 不會被錯誤視為 `Realtime 正常`。

---

# 6. Schedule 模式是否可以自行長期運作？

可以，但要精確區分：

## Static Model 已成功載入後

可以。

列車位置每 5 秒都是 Home Assistant 本機運算，不需要每 5 秒呼叫 TDX。

```text
Static timetable
      ↓
已載入 HA
      ↓
之後列車軌跡本機計算
```

## HA 冷啟動且 TDX Static API 同時完全不可用

目前不保證。

因為 V1 還沒有 persistent offline static cache。

這是未來可靠性強化項目，不影響目前正常網路情境下的 V1 使用。

---

# 7. V1 完成定義

目前可以把以下項目視為正式完成：

```text
A1～A9 實體 LED              ✅
SN74HC595                     ✅
ESPHome renderer              ✅
Home Assistant Static Model   ✅
Schedule trajectory           ✅
普通 / 直達                   ✅
多車                          ✅
方向切換                      ✅
Frame A / Frame B             ✅
Animated Dashboard            ✅
TDX Live ingestion            ✅
Stale detection               ✅
Schedule fallback             ✅
```

不應把以下功能描述成完全驗證：

```text
Fresh Live train matching     🟡
Realtime delay correction     🟡
Offline static cache          ⬜
```

---

# 8. 下一個合理里程碑

優先順序：

1. 等 TYMC LiveBoard 恢復正常新鮮資料。
2. 驗證 realtime matching。
3. 驗證 delay correction。
4. 驗證 stale 40 秒自動退出。
5. 若需要更高可靠度，再加入 static model local cache。

除上述項目外，目前沒有必要重做 V1 UI 或硬體。
