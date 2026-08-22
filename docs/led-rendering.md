# LED 顯示與動畫邏輯

本文件說明 Home Assistant 的列車位置如何轉換成 A1～A9 九顆實體 LED。

---

# 1. 設計限制

實體板只有：

```text
A1 A2 A3 A4 A5 A6 A7 A8 A9
●  ●  ●  ●  ●  ●  ●  ●  ●
```

每個站只有一個離散 LED。

所以無法像螢幕一樣真的把列車畫在：

```text
A5 ─────── ● ─────── A6
```

因此需要用時間上的動畫表示站間位置。

---

# 2. Tracker 每班列車的基本位置

## 到站

```yaml
state: station
station: A5
```

## 站間

```yaml
state: between
from: A5
to: A6
progress: 0.58
```

`progress`：

```text
0.0 = 剛離開 from
1.0 = 即將到達 to
```

---

# 3. Frame A / Frame B

Home Assistant 會產生：

```text
sensor.tymetro_led_frame_a
sensor.tymetro_led_frame_b
```

每個都是：

```text
0 ～ 511
```

也就是 9-bit mask。

---

# 4. 到站顯示

列車在 A5：

```text
Frame A：A5 ON
Frame B：A5 ON
```

ESPHome 即使 A/B 交替：

```text
A5 → A5 → A5 → A5
```

所以肉眼看到的是：

```text
A5 穩定亮
```

---

# 5. 站間動畫

A5 → A6 被分成三個視覺區段。

## 前段

列車還靠近 A5：

```text
Frame A：A5
Frame B：A5
```

A5 穩定亮。

## 中段

列車真正位於兩站中間：

```text
Frame A：A5
Frame B：A6
```

ESP8266：

```text
A5 → 600ms → A6 → 600ms → A5...
```

肉眼理解為：

```text
列車正在 A5 / A6 之間
```

## 後段

列車已靠近 A6：

```text
Frame A：A6
Frame B：A6
```

A6 穩定亮。

---

# 6. 為什麼是 600 ms？

太快：

```text
100～200 ms
```

可能只看成兩顆一起閃或視覺混合。

太慢：

```text
1.5～2 秒
```

會感覺像兩個不相關的狀態。

目前實機使用：

```text
600 ms
```

可以清楚辨識：

```text
A5 ↔ A6
```

且不會太急促。

---

# 7. 為什麼不讓 Home Assistant 每 600 ms 更新？

如果 HA 每 600 ms：

```text
更新 Entity
→ API 傳給 ESPHome
→ Switch 更新
→ 再下一次
```

會製造大量沒有必要的 HA state churn。

所以正確切法：

```text
Home Assistant
每 5 秒
 ↓
Frame A / B

ESPHome
每 600 ms
 ↓
本機交替 Frame
```

這樣：

- HA 負責低頻邏輯
- ESP8266 負責高頻動畫

---

# 8. Bit Mapping

```text
bit 0 = A1
bit 1 = A2
bit 2 = A3
bit 3 = A4
bit 4 = A5
bit 5 = A6
bit 6 = A7
bit 7 = A8
bit 8 = A9
```

例如：

```text
A1 = 1 << 0 = 1
A5 = 1 << 4 = 16
A9 = 1 << 8 = 256
```

---

# 9. 多車如何合併？

假設：

```text
Train 1 = A2
Train 2 = A5
Train 3 = A7→A8 中段
```

Train 1：

```text
Frame A = A2
Frame B = A2
```

Train 2：

```text
Frame A = A5
Frame B = A5
```

Train 3：

```text
Frame A = A7
Frame B = A8
```

合併：

```text
Frame A = A2 + A5 + A7
Frame B = A2 + A5 + A8
```

因此所有 train mask 使用 bitwise OR。

---

# 10. 物理 LED 的資訊限制

如果兩班列車剛好同時在 A5：

```text
Train 1 → A5
Train 2 → A5
```

實體上仍然只會看到：

```text
A5 一顆燈亮
```

無法知道是 1 班還是 2 班。

這是硬體本身的資訊限制。

Dashboard 則可以同時顯示兩個 marker。

---

# 11. Direction

V1 只有一排 LED，所以一次只顯示一個方向：

```text
← 往 A1 台北
```

或：

```text
往 A9 林口 →
```

方向由：

```text
input_select.tymetro_direction
```

控制。

實體 LED 本身不另外用閃爍 encode 方向。

---

# 12. 普通 / 直達

實體 LED 也不 encode：

```text
普通
直達
```

因為一排九顆 LED 最重要的是快速看懂：

> 「列車在哪裡」

若加入：

- 不同閃爍頻率
- 不同 pulse
- 複雜 blink code

會讓位置判讀變得更困難。

普通 / 直達留給 Dashboard 顯示。

---

# 13. 直達車不停 A2，為什麼 A2 還可能亮？

因為 LED 表示物理位置。

例如直達車：

```text
A1 → A3
```

它雖然不停 A2，但軌道仍經過 A2 區域。

所以位置模型仍會經過：

```text
A1 → A2 → A3
```

只是 timetable model 不會建立 A2 停站 dwell。

---

# 14. ESPHome Renderer

每 600 ms：

1. 確認 renderer 未 paused。
2. 確認 Frame A/B 不是 NaN。
3. 依 phase 選 Frame A 或 B。
4. 把 integer 拆成 9 個 bit。
5. 比對目前 switch state。
6. 只有狀態不同才切換。
7. phase 反轉。

概念：

```cpp
mask = phase ? frame_b : frame_a;

A1 = mask & (1 << 0);
A2 = mask & (1 << 1);
...
A9 = mask & (1 << 8);
```

---

# 15. Dashboard 為什麼不直接照 Frame A/B 閃？

因為 Dashboard 沒有九顆 LED 的限制。

Tracker 本身已經知道：

```text
from
to
progress
```

所以 Web UI 可以直接用：

```text
x = x(from) + progress × (x(to) - x(from))
```

畫出連續位置。

然後在每 5 秒資料更新之間用 CSS transition 平滑補間。

因此：

```text
實體 LED = 離散位置 + 600ms 時間動畫
Dashboard = 真正連續位置動畫
```

兩者都源自同一套 Tracker Model，但選擇最適合各自媒介的呈現方式。
