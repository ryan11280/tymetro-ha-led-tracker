# Home Assistant 必要輔助工具（Helpers）

請從 Home Assistant：

```text
設定
→ 裝置與服務
→ 輔助工具
```

建立以下三個 Helper。

---

# 1. 行駛方向

類型：

```text
下拉式選單 / Input Select
```

名稱：

```text
TYMetro Direction
```

Entity ID：

```text
input_select.tymetro_direction
```

Options **必須完全一致**：

```text
← 往 A1 台北
往 A9 林口 →
```

Tracker 會直接使用這兩個字串。

---

# 2. 即時模式（Live Mode）

類型：

```text
切換 / Input Boolean
```

名稱：

```text
TYMetro Live Mode
```

Entity ID：

```text
input_boolean.tymetro_live_mode
```

意義：

```text
OFF
→ 只使用 Schedule 時刻表模擬

ON
→ 啟用 TDX LiveBoard
→ 嘗試 Realtime correction
```

Live Mode 不會取代 Schedule backbone。

---

# 3. 即時工作階段計時器

類型：

```text
Timer
```

名稱：

```text
TYMetro Live Session
```

Entity ID：

```text
timer.tymetro_live_session
```

Duration：

```text
00:15:00
```

建議不要讓 Timer 跨 Home Assistant restart 恢復。

Live Mode 應該：

```text
由使用者主動開啟
+
最多 15 分鐘
```

而不是 HA 重啟後自動繼續 polling TDX。
