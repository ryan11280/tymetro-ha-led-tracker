# 變更紀錄

## 2026-08-22 — v0.1.1-zh-TW

### 文件

- Repository 說明全面改為繁體中文。
- README 改寫成中文 Side Project 專案介紹。
- 補強實體 A1～A9 LED 的硬體架構、Breadboard 位置與運作方式。
- 補充 Frame A / Frame B 站間動畫說明。
- 補充 Schedule、Live Mode、TDX stale fallback、可靠性限制。
- 補充公開 GitHub 前的安全性注意事項。
- 保留程式碼、Entity ID、API field、檔名等必要英文技術識別字。

### 功能

本版主要為文件整理，不修改核心 Tracker 邏輯。

---

## 2026-08-22 — v0.1.0

### 已加入 / 完成

- Home Assistant A1～A9 Schedule trajectory tracker
- 普通車 / 直達車運行模型
- 每 5 秒本機 Tracker Engine
- 兩個 9-bit LED Frame
- ESPHome 600 ms renderer
- NodeMCU + SN74HC595 九顆實體 LED 原型
- A1～A8 由 74HC595 輸出
- A9 由 GPIO16 直接輸出
- All LEDs On / Off
- Chase Test
- 方向選擇
- 15 分鐘 Live Mode
- TDX Static Model
- TDX LiveBoard ingestion
- LiveBoard freshness validation
- Schedule fallback
- Stale Live abort automation
- Animated Lovelace Custom Card V2
- 安裝、架構、硬體、除錯、安全性文件

### 驗證狀態

- Schedule 路徑端到端驗證完成。
- 實體 LED 路徑端到端驗證完成。
- Dashboard 多車顯示驗證完成。
- LiveBoard stale rejection 驗證完成。
- Fresh LiveBoard train matching 仍待 TYMC 上游恢復正常後實測。

### 文件修正

74HC595 旁的 `0.1 µF` 去耦電容改為「建議項目」，不宣稱目前 Breadboard 已實際安裝。
