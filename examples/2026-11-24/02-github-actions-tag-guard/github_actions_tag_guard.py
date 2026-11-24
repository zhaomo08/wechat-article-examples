#!/usr/bin/env python3
"""
GitHub Actions Tag Release & Supply Chain Security Guard Prototype
基于 codex2api 供应链投毒事件复盘构建的 CI/CD 安全审查与 Tag 门禁审计原型
演示未保护 Tag 触发 RCE / Secrets 泄露 vs 最小权限环境隔离与签名防护
"""

import json
import re
from typing import Dict, List, Tuple

# 模拟脆弱的 GitHub Actions 工作流配置 (codex2api 真实失陷模式)
VULNERABLE_WORKFLOW = {
    "name": "Release Docker and Binaries",
    "on": {
        "push": {
            "tags": ["v*"]  # 危险：监听任意 v 开头 Tag，无分支和 Tag 保护约束
        }
    },
    "jobs": {
        "build_and_publish": {
            "runs-on": "ubuntu-latest",
            # 危险：未配置 environment 审批门禁，所有 Secrets 默认注入
            "env": {
                "DOCKERHUB_TOKEN": "${{ secrets.DOCKERHUB_TOKEN }}",
                "RELEASE_API_KEY": "${{ secrets.RELEASE_API_KEY }}",
                "ADMIN_SECRET": "${{ secrets.ADMIN_SECRET }}",
                "PROD_DEPLOY_KEY": "${{ secrets.PROD_DEPLOY_KEY }}"
            },
            "steps": [
                {"name": "Checkout code", "uses": "actions/checkout@v4"},
                {"name": "Build Binary", "run": "make build"},
                {"name": "Publish Docker", "run": "docker build -t app:latest . && docker push app:latest"}
            ]
        }
    }
}

# 模拟经过安全加固的生产级工作流规范 (Hardened CI/CD)
HARDENED_WORKFLOW = {
    "name": "Hardened Release Pipeline",
    "on": {
        "push": {
            "tags": ["v[0-9]+.[0-9]+.[0-9]+"]
        }
    },
    "jobs": {
        "release": {
            "runs-on": "ubuntu-latest",
            "environment": "production-release",  # 关键：绑定受保护的 Environment，必须人工审批
            "permissions": {
                "contents": "write",
                "id-token": "write",  # 推荐使用 OIDC 代替长期静态密钥
                "packages": "write"
            },
            "steps": [
                {"name": "Checkout signed commit", "uses": "actions/checkout@v4", "with": {"ref": "${{ github.ref }}"}},
                {"name": "Verify Tag Signature", "run": "git tag -v ${{ github.ref_name }}"},
                {"name": "Build with Provenance", "run": "make build"},
                {"name": "Push by Digest", "run": "docker build --provenance=true -t app@sha256:immutable ."}
            ]
        }
    }
}

def audit_workflow_security(workflow: Dict, repo_security_rules: Dict) -> Tuple[bool, List[str]]:
    flaws = []
    
    # 1. 检查 Tag 触发条件与仓库 Tag Protection 状态
    push_cfg = workflow.get("on", {}).get("push", {})
    tags = push_cfg.get("tags", [])
    if tags:
        if not repo_security_rules.get("tag_protection_enabled", False):
            flaws.append("🚨 [高危] 工作流由 Tag 推送触发，但仓库未配置 Tag Protection Rules！任何拥有 push 权限的协作者或失陷账号均可绕开 PR 直接触发生产构建。")
        if not repo_security_rules.get("require_signed_tags", False):
            flaws.append("⚠️ [中危] 仓库未强制 GPG/SSH Tag 签名验证，无法防范篡改作者身份的伪造标签。")

    # 2. 检查 Job 级别的环境隔离与 Secrets 范围
    jobs = workflow.get("jobs", {})
    for job_name, job_cfg in jobs.items():
        env_field = job_cfg.get("environment")
        if not env_field:
            flaws.append(f"🚨 [高危] Job `{job_name}` 直接读取仓库级 Secrets，未配置 `environment` 保护！发生投毒时，所有 16+ 个凭据将被一次性外泄。")
        
        # 检查是否使用了高危静态 Token
        env_vars = job_cfg.get("env", {})
        high_risk_keys = [k for k in env_vars.keys() if "KEY" in k or "TOKEN" in k or "SECRET" in k]
        if high_risk_keys and not env_field:
            flaws.append(f"🚨 [严重] Job `{job_name}` 注入了高敏感长期凭据 {high_risk_keys}，缺乏 OIDC 无密认证或环境锁。")

        # 检查是否推送了 :latest 镜像
        steps = job_cfg.get("steps", [])
        for s in steps:
            run_cmd = s.get("run", "")
            if ":latest" in run_cmd:
                flaws.append(f"⚠️ [警告] 步骤 `{s.get('name')}` 推送了 `:latest` 镜像标签！下游用户极易因自动拉取 latest 瞬间被投毒沦陷。")

    passed = len(flaws) == 0
    return passed, flaws


def main():
    print("=" * 68)
    print("  GitHub Actions Tag 发布流水线供应链安全审查器 (Supply Chain Guard)")
    print("=" * 68)

    # 场景 1：脆弱的开源项目默认配置 (codex2api 受害典型)
    print("\n▶ 正在扫描: 【脆弱开源工作流 (无 Tag 保护、无环境隔离、明文 Secrets 注入)】")
    repo_unsafe = {"tag_protection_enabled": False, "require_signed_tags": False}
    passed_unsafe, flaws_unsafe = audit_workflow_security(VULNERABLE_WORKFLOW, repo_unsafe)
    
    print(f"   [安全审计状态]: {'PASS' if passed_unsafe else 'FAIL (检测到严重安全漏洞)'}")
    for f in flaws_unsafe:
        print(f"     {f}")
    print("   >>> 风险模拟: 黑客推送 tag `v3.1.11` -> GitHub Actions 自动构建带后门镜像 -> 窃取 16 个 Secrets 并投毒下游用户！")

    # 场景 2：加固后的生产级发布流水线
    print("\n▶ 正在扫描: 【加固型 CI/CD 工作流 (Tag 保护 + 签名验证 + Environment 审批隔离)】")
    repo_safe = {"tag_protection_enabled": True, "require_signed_tags": True}
    passed_safe, flaws_safe = audit_workflow_security(HARDENED_WORKFLOW, repo_safe)
    
    print(f"   [安全审计状态]: {'PASS (符合供应链安全最佳实践)' if passed_safe else 'FAIL'}")
    if passed_safe:
        print("     ✅ 已启用 Tag Protection: 只有组织 Admin 且经过 2FA 才能推送 Release 标签")
        print("     ✅ 已启用 GPG 签名强制核验: 伪造 Tag 会在第一步失败阻断")
        print("     ✅ 已绑定 `production-release` 环境锁: 触发发布必须经 Security Team 人工审批")
        print("     ✅ 使用 OIDC 与不可变 Digest 镜像哈希: 彻底终结 Secrets 泄露与 latest 自动感染")
        print("   >>> 结果: 黑客恶意推 Tag 尝试在 GitHub 协议层直接被拒绝（Remote rejected: Tag protected）！")

    print("\n" + "=" * 68)
    print("防范清单:")
    print("1. Settings -> Tags -> Add Tag Protection Rule: 锁死 `v*`，禁止非管理员直接 push；")
    print("2. 生产 Release 必须配置 Settings -> Environments 并指定 Required Reviewers；")
    print("3. 服务端部署一律锁定镜像 Digest 哈希，严禁生产环境裸跑 `:latest`。")
    print("=" * 68)

if __name__ == "__main__":
    main()
