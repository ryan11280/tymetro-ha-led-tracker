#!/usr/bin/env python3
"""公開 Repository 前的基本敏感資訊檢查器。

此工具刻意保持簡單且不依賴外部套件，用來抓常見的 Credential、私人網路位址與其他可能誤提交的敏感資訊。
它只能作為輔助檢查，不能保證 Repository 絕對安全；公開前仍應另外檢查完整 Git History。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEXT_EXTENSIONS = {
    ".md", ".yaml", ".yml", ".py", ".js", ".json", ".txt", ".toml", ".ini", ".cfg", ".sh"
}

SKIP_DIRS = {".git", ".esphome", "__pycache__", "node_modules"}

PLACEHOLDER_WORDS = {
    "YOUR_CLIENT_ID",
    "YOUR_CLIENT_SECRET",
    "YOUR_WIFI_SSID",
    "YOUR_WIFI_PASSWORD",
    "GENERATE_A_NEW_ESPHOME_API_KEY",
    "CHANGE_ME",
}

PATTERNS = [
    (
        "私人 IPv4 位址",
        re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
    ),
    (
        "Email 位址",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    ),
    (
        "疑似 Home Assistant Long-Lived Token",
        re.compile(r"\beyJ[A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b"),
    ),
]

ASSIGNMENT_PATTERNS = [
    ("client_secret", re.compile(r"client_secret\s*[=:]\s*['\"]?([^'\"&\s]+)", re.I)),
    ("client_id", re.compile(r"client_id\s*[=:]\s*['\"]?([^'\"&\s]+)", re.I)),
    ("password", re.compile(r"(?:password|passwd)\s*:\s*['\"]?([^'\"\s#]+)", re.I)),
    ("Encryption Key", re.compile(r"(?:encryption[_ -]?key|tymetro_api_encryption_key)\s*:\s*['\"]?([^'\"\s#]+)", re.I)),
]

ALLOWED_ASSIGNMENT_VALUES = PLACEHOLDER_WORDS | {
    "!secret",
    "YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET",
}


def should_scan(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    if path.name == "public-safety-check.py":
        return False  # 不掃描本檔自身的 Regex 範例
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {".gitignore"}


def placeholder_context(line: str) -> bool:
    return any(word in line for word in PLACEHOLDER_WORDS) or "!secret" in line


def main() -> int:
    findings: list[str] = []

    # 不應出現在公開 Repository 的敏感檔名。
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name == "secrets.yaml":
            findings.append(f"{rel}: 發現真正的 secrets.yaml 檔名")
        if path.suffix.lower() in {".pem", ".p12", ".pfx"}:
            findings.append(f"{rel}: 發現可能的 Private Key / Certificate Container")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if not should_scan(rel):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for lineno, line in enumerate(text.splitlines(), 1):
            if placeholder_context(line):
                # Placeholder / example 是刻意公開的範例。
                continue

            for label, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{lineno}: 可能包含 {label}: {line.strip()[:180]}")

            # ESPHome Encryption Key 常以 YAML `key:` 表示。
            # 只對看起來像真實長金鑰的內容提出警告。
            yaml_key = re.match(r"^\s*key:\s*['\"]?([A-Za-z0-9+/]{32,}={0,2})['\"]?\s*$", line)
            if yaml_key:
                findings.append(f"{rel}:{lineno}: 可能包含明文 Encryption Key: {line.strip()[:180]}")

            for label, pattern in ASSIGNMENT_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                value = match.group(1)
                if value in ALLOWED_ASSIGNMENT_VALUES or value.startswith("{{"):
                    continue
                # YAML `!secret` 是合法的安全引用。
                if "!secret" in line:
                    continue
                findings.append(f"{rel}:{lineno}: 可能包含明文 {label}: {line.strip()[:180]}")

    if findings:
        print("公開安全檢查：需要人工確認")
        for item in findings:
            print(f" - {item}")
        print("\n此工具是啟發式掃描。請逐項確認結果，並另外掃描完整 Git History。")
        return 1

    print("公開安全檢查：PASS")
    print("目前工作目錄未偵測到明顯的明文 Credential、私人 IPv4 位址或個人 Email。")
    print("若這是原本的 Private Repository，改成 Public 前仍需另外檢查完整 Git History。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
