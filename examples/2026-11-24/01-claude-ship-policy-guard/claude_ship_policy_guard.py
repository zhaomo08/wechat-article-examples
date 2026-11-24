#!/usr/bin/env python3
"""
Claude Ship Automated PR Approval Policy Guard Prototype
模拟 Claude Ship (Claude Approvals) 自动化 PR 审核策略引擎
演示低风险变更自动放行 (Auto-Approve) 与高风险敏感变更强阻断 (Block & Escalate) 的分级策略执行
"""

import json
import re
from typing import Dict, List, Tuple

# 声明式仓库策略规范 (Policy-as-Code)
DEFAULT_POLICY = {
    "version": "1.0",
    "name": "Backend-Production-Guardrail",
    "rules": {
        "max_diff_lines_auto_approve": 150,
        "required_test_coverage_pass": True,
        "restricted_paths": [
            r"^src/auth/.*",
            r"^src/payment/.*",
            r"^migrations/.*\.sql$",
            r"^\.github/workflows/.*",
            r"^infra/terraform/.*",
            r"^config/security.*"
        ],
        "allowed_auto_approve_patterns": [
            r"^docs/.*",
            r"^tests?/.*",
            r".*\.md$",
            r".*\.lock$",
            r"^src/ui/styles/.*\.css$",
            r"^types/.*\.d\.ts$"
        ]
    }
}

class PRChange:
    def __init__(self, pr_id: int, title: str, author: str, files: List[Dict], tests_passed: bool):
        self.pr_id = pr_id
        self.title = title
        self.author = author
        self.files = files
        self.tests_passed = tests_passed

    @property
    def total_lines_changed(self) -> int:
        return sum(f.get("additions", 0) + f.get("deletions", 0) for f in self.files)

def evaluate_pr_policy(pr: PRChange, policy: Dict) -> Tuple[bool, str, List[str]]:
    reasons = []
    rules = policy["rules"]

    # 1. 基础门禁：CI 测试是否通过
    if rules["required_test_coverage_pass"] and not pr.tests_passed:
        reasons.append("❌ CI 测试检查未通过或存在挂起用例，禁止自动审批")
        return False, "REJECTED_CI_FAILED", reasons

    # 2. 变更规模检查
    max_lines = rules["max_diff_lines_auto_approve"]
    if pr.total_lines_changed > max_lines:
        reasons.append(f"⚠️ 变更行数 ({pr.total_lines_changed} lines) 超出免审阈值 ({max_lines} lines)")

    # 3. 敏感路径受限检查
    restricted_hits = []
    for f in pr.files:
        path = f["path"]
        for pattern in rules["restricted_paths"]:
            if re.match(pattern, path):
                restricted_hits.append((path, pattern))
                break

    if restricted_hits:
        reasons.append(f"🚨 触碰核心敏感路径 ({len(restricted_hits)} 处)，必须由业务负责人人工审计：")
        for p, pat in restricted_hits:
            reasons.append(f"   - 文件: `{p}` 命中受限规则 `{pat}`")
        return False, "ESCALATE_TO_HUMAN", reasons

    # 4. 白名单路径校验
    allowed_patterns = rules["allowed_auto_approve_patterns"]
    non_whitelisted_files = []
    for f in pr.files:
        path = f["path"]
        is_whitelisted = any(re.match(p, path) for p in allowed_patterns)
        if not is_whitelisted:
            non_whitelisted_files.append(path)

    if non_whitelisted_files and pr.total_lines_changed > max_lines:
        reasons.append(f"⚠️ 包含非白名单业务逻辑修改且超过行数上限，需人工确认: {non_whitelisted_files[:3]}")
        return False, "REQUIRE_PEER_REVIEW", reasons

    if not reasons:
        reasons.append(f"✅ 符合低风险免审策略 (受限路径 0 命中，变更规模 {pr.total_lines_changed} <= {max_lines}，CI 全绿)")
        return True, "AUTO_APPROVED", reasons

    return False, "MANUAL_REVIEW_REQUIRED", reasons


def main():
    print("=" * 68)
    print("  Claude Ship (Claude Approvals) 策略守卫模拟器 (Policy-as-Code)")
    print("=" * 68)

    # 模拟场景 A：日常低风险修补（文档、测试、类型注解）
    pr_safe = PRChange(
        pr_id=1042,
        title="fix(types): update payment response interface & add mock tests",
        author="claude-code-bot",
        files=[
            {"path": "types/payment.d.ts", "additions": 14, "deletions": 2},
            {"path": "tests/unit/payment_mock_test.py", "additions": 45, "deletions": 5},
            {"path": "docs/api_v2_migration.md", "additions": 20, "deletions": 0}
        ],
        tests_passed=True
    )

    # 模拟场景 B：高风险核心逻辑篡改（包含鉴权中间件与 SQL 迁移，但 CI 测试全绿）
    pr_dangerous = PRChange(
        pr_id=1043,
        title="perf(auth): optimize token validation cache & add db index",
        author="ai-assistant-worker",
        files=[
            {"path": "src/auth/jwt_validator.py", "additions": 80, "deletions": 30},
            {"path": "migrations/20261124_add_user_auth_index.sql", "additions": 12, "deletions": 0},
            {"path": "tests/test_auth_perf.py", "additions": 35, "deletions": 0}
        ],
        tests_passed=True
    )

    # 运行评估
    test_cases = [("场景 1: AI 提交低风险修复 (文档/单测/类型定义)", pr_safe),
                  ("场景 2: AI 提交核心鉴权与数据库变更 (语法测试全绿)", pr_dangerous)]

    for scenario_name, pr in test_cases:
        print(f"\n▶ 正在审核: 【{scenario_name}】")
        print(f"   PR #{pr.pr_id} - '{pr.title}' (作者: {pr.author})")
        print(f"   变更文件数: {len(pr.files)} | 变更总行数: {pr.total_lines_changed} | CI状态: {'PASSED' if pr.tests_passed else 'FAILED'}")

        approved, status, details = evaluate_pr_policy(pr, DEFAULT_POLICY)

        print(f"   [策略引擎决策]: {status}")
        for d in details:
            print(f"     {d}")

        if approved:
            print("   >>> 结果: [PASS] 触发 Claude Ship 自动 Approve 并进入快速合并通道！")
        else:
            print("   >>> 结果: [BLOCKED] 触发生产安全熔断，强制转为人工 Senior Reviewer 签批！")

    print("\n" + "=" * 68)
    print("结论: AI 时代 PR 审批绝不能裸奔，策略代码化 (Policy-as-Code) 是团队核心生命线。")
    print("=" * 68)

if __name__ == "__main__":
    main()
