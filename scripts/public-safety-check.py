#!/usr/bin/env python3
"""Conservative public-repository sanity scanner.

This is intentionally small and dependency-free. It catches common accidental
secrets/network identifiers, but it cannot prove that a repository is safe.
Always review Git history with a dedicated secret scanner before going public.
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
        "private IPv4 address",
        re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
    ),
    (
        "email address",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    ),
    (
        "Home Assistant long-lived token-like value",
        re.compile(r"\beyJ[A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b"),
    ),
]

ASSIGNMENT_PATTERNS = [
    ("client_secret", re.compile(r"client_secret\s*[=:]\s*['\"]?([^'\"&\s]+)", re.I)),
    ("client_id", re.compile(r"client_id\s*[=:]\s*['\"]?([^'\"&\s]+)", re.I)),
    ("password", re.compile(r"(?:password|passwd)\s*:\s*['\"]?([^'\"\s#]+)", re.I)),
    ("encryption key", re.compile(r"(?:encryption[_ -]?key|tymetro_api_encryption_key)\s*:\s*['\"]?([^'\"\s#]+)", re.I)),
]

ALLOWED_ASSIGNMENT_VALUES = PLACEHOLDER_WORDS | {
    "!secret",
    "YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET",
}


def should_scan(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    if path.name == "public-safety-check.py":
        return False  # don't flag the scanner's own regex examples
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {".gitignore"}


def placeholder_context(line: str) -> bool:
    return any(word in line for word in PLACEHOLDER_WORDS) or "!secret" in line


def main() -> int:
    findings: list[str] = []

    # Sensitive filenames that should never exist in this repository tree.
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name == "secrets.yaml":
            findings.append(f"{rel}: real secrets.yaml filename present")
        if path.suffix.lower() in {".pem", ".p12", ".pfx"}:
            findings.append(f"{rel}: private-key/certificate container file present")

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
                # Placeholder/example lines are intentionally public.
                continue

            for label, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{lineno}: possible {label}: {line.strip()[:180]}")

            # ESPHome encryption keys are often represented as a plain YAML `key:`
            # under `api.encryption`. Flag only values that actually look like long key material.
            yaml_key = re.match(r"^\s*key:\s*['\"]?([A-Za-z0-9+/]{32,}={0,2})['\"]?\s*$", line)
            if yaml_key:
                findings.append(f"{rel}:{lineno}: possible literal encryption key: {line.strip()[:180]}")

            for label, pattern in ASSIGNMENT_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                value = match.group(1)
                if value in ALLOWED_ASSIGNMENT_VALUES or value.startswith("{{"):
                    continue
                # YAML !secret is usually captured as the first token; allow it.
                if "!secret" in line:
                    continue
                findings.append(f"{rel}:{lineno}: possible literal {label}: {line.strip()[:180]}")

    if findings:
        print("PUBLIC SAFETY CHECK: REVIEW REQUIRED")
        for item in findings:
            print(f" - {item}")
        print("\nThis script is heuristic. Review each result and scan Git history separately.")
        return 1

    print("PUBLIC SAFETY CHECK: PASS")
    print("No obvious literal credentials, private IPv4 addresses, or personal email addresses were found in the current working tree.")
    print("Still scan Git history before making an existing repository public.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
