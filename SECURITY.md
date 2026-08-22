# 安全性說明

這個 Repository 設計成可以公開展示，但**只能保存已去除敏感資訊的設定範例**。

---

## 絕對不要提交到 Git 的資料

不要把以下內容放進 Git：

- TDX Client ID
- TDX Client Secret
- TDX OAuth Access Token
- Home Assistant Long-Lived Access Token
- ESPHome Native API Encryption Key
- Wi-Fi 真實密碼
- ESPHome Fallback Hotspot 真實密碼
- TLS Private Key
- 私人憑證
- 個人 Home Assistant 完整設定
- 不相關的私人 IP / Email / 地址資訊

---

# Home Assistant Secrets

實際環境中的：

```text
/homeassistant/secrets.yaml
```

應保持私有。

本專案會使用：

```yaml
tdx_auth_payload: 'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET'
```

而 `configuration.yaml` 只引用：

```yaml
payload: !secret tdx_auth_payload
```

**不要把真正的 `secrets.yaml` 上傳 GitHub。**

---

# ESPHome Secrets

公開 Repository 只放：

```text
esphome/secrets.example.yaml
```

例如：

```yaml
wifi_ssid: "YOUR_WIFI_SSID"
wifi_password: "YOUR_WIFI_PASSWORD"
tymetro_api_encryption_key: "GENERATE_A_NEW_ESPHOME_API_KEY"
tymetro_fallback_password: "CHANGE_ME"
```

實際使用值應放在 ESPHome 私有的 secrets 機制中。

---

# 憑證輪替原則

如果任何 Credential 曾經完整出現在：

- Chat
- Screenshot
- Issue
- Gist
- Log
- Paste
- Commit
- Public forum

就應該視為「已曝光過」，並重新產生。

尤其建議公開 repo 前重新產生：

- ESPHome API encryption key
- ESPHome fallback AP password
- TDX Client Secret（若不確定是否曾公開）

---

# Git 歷史紀錄特別注意

把最新版本的密碼刪掉，**不代表舊 Commit 裡的密碼消失**。

例如：

```text
Commit 1：password = abc123
Commit 2：改成 !secret
```

Repository 公開之後，別人仍可以查看 Commit 1。

因此原本是 Private、準備改 Public 時，必須檢查完整 Git History。

---

# Repository 內建安全掃描

執行：

```bash
python scripts/public-safety-check.py
```

它會檢查一些常見的：

- Literal credential
- 私人 IPv4
- Email
- 可疑 Secret pattern

但它只能做基本 pattern scan，**不能保證所有任意格式的 secret 都一定被找到**。

---

# 公開前建議

依序確認：

1. Repository working tree 沒有真實 secret。
2. `secrets.yaml` 不在 Git。
3. `.gitignore` 正常。
4. 完整 Git history 沒有歷史 secret。
5. Dashboard screenshot 沒有 Token / IP / Email / 地址。
6. 曾經曝光過的 credential 已 rotate。
7. GitHub Secret Scanning 沒有警告。

完整清單請看：

[docs/public-release-checklist.md](docs/public-release-checklist.md)
