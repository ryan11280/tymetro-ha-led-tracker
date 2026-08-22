# TDX 資料設計

本專案使用 TDX 桃園捷運資料，但刻意把 Static 與 Live 分開。

---

# 1. OAuth

使用：

```text
Client Credentials
```

Token Endpoint：

```text
https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token
```

實際 Client ID / Secret 放在 HA `secrets.yaml`。

程式不假設 token 固定能用多久，而是讀 TDX 回傳資訊；目前設定以較保守週期刷新。

---

# 2. Static APIs

## S2STravelTime

用途：

```text
站到站 RunTime
StopTime
TrainType
```

Tracker 用它建立列車的物理行駛時間軸。

---

## StoppingPattern

用途：

```text
TrainType
StoppingPatternID
停靠站
```

目前觀察到：

```text
TrainType 1 → 普通車
TrainType 2 → 直達車
```

不同 Stopping Pattern 可能對應不同營運情境。

---

## StationTimeTable A1

用作往 A9 方向 schedule anchor。

---

## StationTimeTable A8

用作往 A1 方向 schedule anchor。

A8 同時是直達車的重要停靠站，因此適合建立不同 TrainType 的時間軸。

---

# 3. LiveBoard

Endpoint：

```text
Rail/Metro/LiveBoard/TYMC
```

V1 只保存：

```text
A1～A9
```

records。

常見欄位：

```text
StationID
TripHeadSign
DestinationStaionID
DestinationStationID
ServiceStatus
EstimateTime
SrcUpdateTime
UpdateTime
```

注意資料中可能同時存在：

```text
DestinationStaionID
DestinationStationID
```

其中前者拼字是來源資料既有欄位，不應自行假設所有資料只會有其中一種。

---

# 4. LiveBoard 的核心限制

LiveBoard 是 station-centric ETA。

不是 GPS。

它通常沒有穩定提供：

```text
TrainNo
唯一 Train ID
目前線路座標
GPS
```

所以一筆資料比較像：

```text
A8
往 A1
10 分鐘
```

不是：

```text
列車 #1234 位於 A7.4
```

---

# 5. 實際觀察到的 ETA Pattern

例如 A8 往 A1 的資料曾看過兩組交錯 ETA：

```text
10, 25, 41, 56
9, 24, 39, 54
```

這很像不同服務型態的列車序列，但 LiveBoard 本身沒有直接給足夠可靠的 TrainType / Train ID 讓我們簡單一對一辨認。

所以不能寫：

```text
第一個 ETA = 普通
第二個 ETA = 直達
```

當作硬規則。

---

# 6. Live Matching 策略

因此使用 Schedule-first。

流程：

```text
Schedule train candidates
        ↓
預測各班車近期站點到站時間
        ↓
LiveBoard station ETA
        ↓
轉成 absolute ETA
        ↓
依 Station / Direction / Destination / Time Window Matching
        ↓
得到 delay candidates
        ↓
穩健整合
        ↓
修正 schedule timeline
```

---

# 7. 為什麼採保守 Matching？

錯誤 matching 的傷害比不 matching 大。

若錯把：

```text
Train A 的 ETA
```

套到：

```text
Train B
```

Dashboard 與 LED 反而會比 Schedule 更錯。

所以設計原則：

> 不確定就不修正。

可能的 mode：

```text
schedule_live_pending
```

代表 Live Mode 已開，但還沒有可信 correction。

---

# 8. Freshness

LiveBoard HTTP 200 不代表資料新鮮。

目前主要看：

```text
SrcUpdateTime
```

若：

```text
now - SrcUpdateTime > 300 秒
```

進入：

```text
schedule_live_stale
```

---

# 9. 曾實際測到的 stale 情況

某次：

```text
HA fetched_at：22:43 左右
newest SrcUpdateTime：21:47 左右
newest UpdateTime：21:50 左右
records：96
HTTP：200
```

API 可以連，但資料已落後約一小時。

系統正確：

```text
live_correction_active = false
```

並繼續 Schedule。

---

# 10. API 呼叫策略

Static：

```text
HA 啟動
每天 03:30
```

LiveBoard：

```text
Live Mode OFF → 不呼叫
Live Mode ON  → 立即 + 每 30 秒
最多 15 分鐘
```

Tracker Engine：

```text
每 5 秒
```

但那是**本機計算**，不是 TDX API request。

---

# 11. 為什麼不 24/7 LiveBoard？

主要原因：

1. 免費額度有限。
2. Schedule 已足夠當日常模式。
3. LiveBoard 來源本身可能 stale。
4. 使用者真正需要 realtime 時再開即可。
5. 減少無意義 request。

---

# 12. 未來可研究

- TDX `health=true` 或相關 data health metadata
- 更精細的 destination / pattern matching
- 多站 ETA joint matching
- Delay confidence score
- 觀察 TYMC LiveBoard 長期更新品質
