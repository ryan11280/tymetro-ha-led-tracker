# GitHub 公開前檢查清單

將 Repository 從 Private 改成 Public 前，建議完整檢查一次。

---

# 1. Credential

確認不存在真正的：

- [ ] TDX Client ID
- [ ] TDX Client Secret
- [ ] TDX Access Token
- [ ] Home Assistant Token
- [ ] ESPHome API Encryption Key
- [ ] Wi-Fi Password
- [ ] Fallback AP Password
- [ ] TLS Private Key
- [ ] SSH Private Key

---

# 2. Secrets File

確認沒有：

```text
secrets.yaml
.env
*.key
```

等私人檔案被 Git track。

---

# 3. `.gitignore`

確認：

```text
secrets.yaml
.storage/
.esphome/
*.db
*.db-wal
*.db-shm
__pycache__/
```

等 runtime / secret 資料被排除。

---

# 4. Git History

非常重要。

確認不只是最新檔案乾淨，而是：

```text
所有舊 Commit
```

也沒有 secret。

如果歷史 commit 曾有 secret：

1. Rotate credential。
2. 視需要清理 Git history。
3. 不要只刪最新版本。

---

# 5. Screenshot

檢查所有圖片：

- [ ] 沒有 Home Assistant URL
- [ ] 沒有 IP
- [ ] 沒有 Email
- [ ] 沒有 Token
- [ ] 沒有地址
- [ ] 沒有私人通知內容
- [ ] 沒有不希望公開的裝置名稱

目前 Dashboard screenshot 僅呈現 Tracker UI 與其他 Dashboard tab 名稱，不包含 credential。

---

# 6. 程式內 Literal

執行：

```bash
python scripts/public-safety-check.py
```

應得到 PASS。

---

# 7. GitHub Secret Scanning

如果帳號 / Repo 功能可用，查看：

```text
Security
→ Secret scanning
```

確認沒有偵測結果。

---

# 8. 曾出現在其他地方的 Secret

就算不在 repo，如果 Credential 曾出現在：

- Chat
- Screenshot
- Forum
- Paste
- Issue

建議公開專案前直接 rotate。

---

# 9. 個人資訊

確認 README / docs 沒有：

- 真實地址
- 私人電話
- 私人 Email
- 身分證 / 帳號
- 其他不必要的個資

Side Project 不需要這些資訊。

---

# 10. 開源授權

目前 Repository 不一定需要立刻加入 License。

如果只是：

```text
Portfolio / Side Project
```

可以先不放。

若希望別人：

- Fork
- 修改
- 再散布
- 使用程式碼

可考慮加入：

```text
MIT License
```

這是另外的授權決策，與「Public / Private」不同。

---

# 11. 最後判斷

全部確認後，可以把 Repo 作為 Side Project 公開。

建議公開版本 README 清楚標示：

> 本專案不是官方桃園捷運產品，TDX / TYMC 資料品質與可用性由原始資料來源決定。
