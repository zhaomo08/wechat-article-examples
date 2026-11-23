#!/usr/bin/env python3
"""
CLI Agent 上下文预算管理与防翻车守护工具 (CLI Agent Guard)
针对终端智能体（如 Claude Code / Codex / CLI Agent）日常实战痛点：
1. 上下文膨胀速度检测（防 Token 账单突发失控）
2. 敏感受保护文件拦截（防 Git 仓库与本地凭据污染）
3. 单元测试状态机闭环（防'看起来做完了但测试全挂'的虚假交付）
"""

import sys
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class AgentSessionMetrics:
    step_count: int
    current_tokens: int
    max_budget_tokens: int
    modified_files: List[str]
    protected_files: Set[str]
    test_suite_passed: bool

class CLIAgentGuard:
    def __init__(self, token_budget: int = 120_000):
        self.token_budget = token_budget
        self.protected_patterns = {
            ".env", ".publish_token", "id_rsa", "credentials", "pom.xml", "package-lock.json"
        }

    def inspect_session(self, metrics: AgentSessionMetrics) -> Dict[str, any]:
        alerts = []
        status = "PASSED"

        # 1. 上下文健康度检查
        usage_pct = (metrics.current_tokens / self.token_budget) * 100
        if usage_pct > 80.0:
            alerts.append(f"CRITICAL: 上下文消耗达到 {metrics.current_tokens:,} tokens ({usage_pct:.1f}%)，逼近硬上限！必须立即执行 /compact 或拆分子任务。")
            status = "WARNING"
        elif usage_pct > 50.0:
            alerts.append(f"NOTICE: 上下文已达 {metrics.current_tokens:,} tokens ({usage_pct:.1f}%)，建议清理无用输出。")

        # 2. 受保护文件污染检查
        contaminated = []
        for f in metrics.modified_files:
            fname = os.path.basename(f)
            if fname in self.protected_patterns or any(f.endswith(ext) for ext in [".key", ".pem", ".p12"]):
                contaminated.append(f)
        
        if contaminated:
            alerts.append(f"BLOCKED: 检测到终端 Agent 试图修改高危保护文件: {contaminated}！已触发安全熔断。")
            status = "FAILED"

        # 3. 验收标准：测试闭环检查
        if not metrics.test_suite_passed:
            alerts.append("REJECTED: 智能体宣称任务完成，但本地单元测试套件未跑通 (Exit Code != 0)！杜绝'伪完成'。")
            status = "FAILED"

        return {
            "status": status,
            "usage_pct": usage_pct,
            "alerts": alerts,
            "can_commit": status == "PASSED"
        }

def run_simulation():
    guard = CLIAgentGuard(token_budget=100_000)

    print("==================================================================")
    print(" 终端智能体 (CLI Agent) 实战防翻车守护器 Benchmark ")
    print("==================================================================")

    # 案例 A: 踩坑会话 —— 跑了 40 轮，Token 爆炸且修改了密钥，测试未过
    bad_session = AgentSessionMetrics(
        step_count=42,
        current_tokens=89_500,
        max_budget_tokens=100_000,
        modified_files=["src/service/UserService.java", ".env", "config/application.yml"],
        protected_files={".env"},
        test_suite_passed=False
    )

    print(">>> 模拟运行 [案例 A: 典型翻车终端 Agent 会话 (长对话+改敏感文件+测试未跑)]")
    res_a = guard.inspect_session(bad_session)
    print(f"  [审查结果] {res_a['status']}")
    print(f"  [Token 占用] {res_a['usage_pct']:.1f}%")
    for a in res_a['alerts']:
        print(f"  ! {a}")
    print(f"  [准许 Git Commit/Push]: {res_a['can_commit']}\n")

    # 案例 B: 规范纪律会话 —— 小步快跑，单次聚焦，测试全通
    good_session = AgentSessionMetrics(
        step_count=8,
        current_tokens=18_400,
        max_budget_tokens=100_000,
        modified_files=["src/service/OrderService.java", "src/test/OrderServiceTest.java"],
        protected_files=set(),
        test_suite_passed=True
    )

    print(">>> 模拟运行 [案例 B: 规范实战智能体会话 (小步分治+测试驱动+范围受控)]")
    res_b = guard.inspect_session(good_session)
    print(f"  [审查结果] {res_b['status']}")
    print(f"  [Token 占用] {res_b['usage_pct']:.1f}%")
    if not res_b['alerts']:
        print("  ✓ 所有健康指标正常，无越权修改，测试全部通过。")
    print(f"  [准许 Git Commit/Push]: {res_b['can_commit']}\n")

    print("------------------------------------------------------------------")
    print(" 总结：纳德拉谈 VS Code 与终端 Agent 时代的 3 项铁律：")
    print("  1. 上下文预算律：单次会话只解决一个具体问题，超过 50% 预算果断 /compact")
    print("  2. 测试驱动律：不要让人肉当肉眼 linter，让自动化测试当 Agent 的红绿灯")
    print("  3. 权限围栏律：保护核心配置文件与凭证，审查 diff 决不无脑 commit")
    print("==================================================================")

if __name__ == "__main__":
    run_simulation()
