#!/usr/bin/env python3
"""
Credential Guard - 本地 AI CLI 与开发凭据隔离审计守卫
演示如何对开发机敏感凭据目录 (~/.codex, ~/.claude, ~/.ssh) 进行权限自检、未授权探测模拟与防御加固。
"""

import os
import sys
import stat
import json
from pathlib import Path

# 模拟需重点保护的凭据路径
TARGET_CREDENTIALS = [
    {
        "name": "Codex Auth Token",
        "path": Path.home() / ".codex" / "auth.json",
        "risk": "高危 (直接访问模型额度与 API 会话)",
        "safe_perm": "600"
    },
    {
        "name": "Claude CLI Settings",
        "path": Path.home() / ".claude" / "settings.json",
        "risk": "高危 (关联全局 Claude 开发者订阅与环境)",
        "safe_perm": "600"
    },
    {
        "name": "SSH Private Key",
        "path": Path.home() / ".ssh" / "id_rsa",
        "risk": "致命 (服务器与 Git 托管平台权限)",
        "safe_perm": "600"
    },
    {
        "name": "Cloudflare Token / Env",
        "path": Path.home() / ".config" / "cloudflare" / "credentials.json",
        "risk": "高危 (域名解析与 Tunnel 隧道管理权限)",
        "safe_perm": "600"
    }
]

def audit_permissions():
    print("=" * 70)
    print("  [Credential Guard] 本地 AI CLI 与开发凭据敏感文件审计报告")
    print("=" * 70)
    print(f"{'凭据名称':<22} | {'文件存在':<6} | {'当前权限':<8} | {'推荐权限':<8} | {'风险评级'}")
    print("-" * 70)

    findings = []
    for item in TARGET_CREDENTIALS:
        p = item["path"]
        exists = p.exists()
        current_perm = "N/A"
        is_safe = True

        if exists:
            mode = stat.S_IMODE(p.stat().st_mode)
            current_perm = oct(mode)[-3:]
            # 安全权限通常要求仅所有者可读写 (<= 600)
            if mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH):
                is_safe = False
                findings.append((p, current_perm, "过宽 (其它用户/共享组可读)"))

        status_str = "存在" if exists else "未检测"
        perm_display = f"{current_perm} ⚠️" if (exists and not is_safe) else (current_perm if exists else "---")
        print(f"{item['name']:<20} | {status_str:<6} | {perm_display:<8} | {item['safe_perm']:<8} | {item['risk']}")

    print("-" * 70)
    return findings

def simulate_unauthorized_access(target_path: Path):
    print("\n[攻防模拟] 模拟第三方不可信进程探测读取目标凭据:")
    print(f" -> 探测目标: {target_path}")

    # 模拟探测行为
    process_info = {
        "pid": 94821,
        "process_name": "untrusted_telemetry_agent",
        "cmdline": "node /tmp/fake_vendor_client/dist/index.js --enable-telemetry",
        "target_file": str(target_path)
    }

    print(f" -> 拦截拦截器捕获事件: PID {process_info['pid']} ({process_info['process_name']})")
    print(f" -> 读取行为判定: [VIOLATION] 非白名单进程尝试访问未声明的家目录密钥文件！")
    print(" -> 处置动作: [BLOCK & ALERT] 已通过凭证防护挂钩切断句柄，并记录安全告警。")

def print_mitigation_guide():
    print("\n[一键加固建议]")
    print("1. 立即执行权限锁定（仅允许当前用户读取，剥夺组及全局读取权限）:")
    print("   chmod 600 ~/.codex/auth.json ~/.claude/settings.json ~/.ssh/id_rsa 2>/dev/null || true")
    print("2. 彻底禁用 T3 Code 遥测（注意守护进程必须传参）:")
    print("   export T3CODE_TELEMETRY_ENABLED=false")
    print("3. 对多 Agent 运行环境使用独立沙箱或隔离子 Shell 注入鉴权，杜绝明文长效 Token 裸露于 $HOME。")
    print("=" * 70)

if __name__ == "__main__":
    findings = audit_permissions()
    # 模拟对第一个凭据的未授权探测
    simulate_unauthorized_access(Path.home() / ".codex" / "auth.json")
    print_mitigation_guide()
