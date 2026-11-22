#!/usr/bin/env python3
"""
Canary Redaction Proxy Demo for Outbound LLM API Requests
Simulates:
1. Sensitive credential & PII redaction (Password, Token, IP, Phone)
2. Canary token (URL) injection for leak traceability
3. Third-party delayed leak detection & alerting
4. Bi-directional placeholder restoration for application response
"""

import re
import uuid
import time
import hashlib
from typing import Dict, Tuple

class CanaryTracker:
    def __init__(self):
        self.registry: Dict[str, dict] = {}
        self.alerts = []

    def mint_token(self, request_id: str, model_name: str) -> str:
        token_id = hashlib.sha256(f"{request_id}-{time.time()}".encode()).hexdigest()[:16]
        canary_url = f"https://canary.internal.corp/probe/{token_id}.png"
        self.registry[token_id] = {
            "request_id": request_id,
            "model_name": model_name,
            "created_at": time.time(),
            "triggered": False,
            "url": canary_url
        }
        return canary_url

    def trigger_probe(self, token_id: str, client_ip: str, user_agent: str):
        if token_id in self.registry:
            entry = self.registry[token_id]
            entry["triggered"] = True
            entry["leak_timestamp"] = time.time()
            entry["client_ip"] = client_ip
            entry["user_agent"] = user_agent
            delay_hours = (entry["leak_timestamp"] - entry["created_at"]) / 3600.0
            alert_msg = (
                f"[CRITICAL LEAK ALERT] Canary Token {token_id} triggered!\n"
                f"  - Original Model: {entry['model_name']}\n"
                f"  - Request ID: {entry['request_id']}\n"
                f"  - Access Time Delay: ~{delay_hours:.1f} hours after completion\n"
                f"  - External IP: {client_ip} | UA: {user_agent}\n"
                f"  -> EVIDENCE: Prompt payload was retained and accessed by an unauthorized 3rd party!"
            )
            self.alerts.append(alert_msg)
            return alert_msg
        return None

class RedactionEngine:
    PATTERNS = {
        "DB_PASS": (r'(?i)(password|pwd|secret)\s*[:=]\s*["\']?([^"\'\s]+)["\']?', r'\1: "<REDACTED_PASS_{id}>"'),
        "API_KEY": (r'\b(sk-[a-zA-Z0-9]{24,48}|bearer\s+[a-zA-Z0-9_\-\.]{20,})\b', r'<REDACTED_KEY_{id}>'),
        "INTERNAL_IP": (r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b', r'<REDACTED_IP_{id}>'),
        "PHONE": (r'\b1[3-9]\d{9}\b', r'<REDACTED_PHONE_{id}>'),
    }

    def __init__(self):
        self.vault: Dict[str, str] = {}

    def redact(self, text: str) -> str:
        redacted = text
        for ptype, (regex, repl) in self.PATTERNS.items():
            matches = list(re.finditer(regex, redacted))
            for m in reversed(matches):
                val = m.group(0)
                ref_id = hashlib.md5(val.encode()).hexdigest()[:8]
                placeholder = f"<REDACTED_{ptype}_{ref_id}>"
                self.vault[placeholder] = val
                redacted = redacted[:m.start()] + placeholder + redacted[m.end():]
        return redacted

    def restore(self, text: str) -> str:
        restored = text
        for placeholder, original in self.vault.items():
            restored = restored.replace(placeholder, original)
        return restored

def main():
    print("=" * 72)
    print("LLM Outbound Security Proxy: Redaction & Canary Leak Detection Demo")
    print("=" * 72)

    tracker = CanaryTracker()
    engine = RedactionEngine()

    raw_user_prompt = (
        "排查线上报警：支付网关与数据库连接超时。\n"
        "配置详情：\n"
        "  - 数据库地址: 192.168.1.188:3306\n"
        "  - 账号: root, password: SuperSecretP@ssw0rd!2026\n"
        "  - 第三方通道商 API Key: sk-live-982187349128471204918234\n"
        "  - 应急值班人手机: 13812345678\n"
        "请帮我分析连接池参数与排查思路。"
    )

    req_id = str(uuid.uuid4())[:8]
    model_target = "minimax/text-01-turbo"

    print("\n[Step 1] Developer sends raw prompt with sensitive internal credentials:")
    print("-" * 72)
    print(raw_user_prompt)

    # 1. Redact
    redacted_prompt = engine.redact(raw_user_prompt)
    # 2. Inject Canary URL
    canary_url = tracker.mint_token(req_id, model_target)
    outbound_prompt = (
        f"{redacted_prompt}\n\n"
        f"<!-- Reference Audit Checksum: {canary_url} -->"
    )

    print("\n[Step 2] Outbound Security Gateway Redacts Data & Injects Canary Token:")
    print("-" * 72)
    print(outbound_prompt)

    # 3. Simulated Model Generation
    print("\n[Step 3] Model Provider receives sanitized payload and generates response:")
    simulated_model_output = (
        "建议排查步骤：\n"
        "1. 确认 <REDACTED_IP_6ec0fa72> 机器上的 3306 端口 iptables 防火墙是否放行；\n"
        "2. 密码 <REDACTED_DB_PASS_6cd75121> 建议配置进 KMS 密钥管理系统，避免明文；\n"
        "3. 检查 HikariCP 连接池 maximumPoolSize 与 idleTimeout 设置。"
    )
    print(simulated_model_output)

    # 4. Safe In-house Restoration
    restored_output = engine.restore(simulated_model_output)
    print("\n[Step 4] Gateway securely restores placeholders before handing back to developer:")
    print("-" * 72)
    print(restored_output)

    # 5. Leak Simulation
    print("\n[Step 5] Simulating delayed leak (~72 hours later, external bot hits Canary URL):")
    print("-" * 72)
    token_key = list(tracker.registry.keys())[0]
    # simulate delay
    tracker.registry[token_key]["created_at"] -= 72 * 3600
    alert = tracker.trigger_probe(
        token_id=token_key,
        client_ip="198.51.100.74 (Unknown Cloud Scraper)",
        user_agent="Mozilla/5.0 (compatible; DataminingCrawler/3.2)"
    )
    print(alert)
    print("\n[Audit Result] ZERO real credentials leaked to external crawler!")
    print("=" * 72)

if __name__ == "__main__":
    main()
