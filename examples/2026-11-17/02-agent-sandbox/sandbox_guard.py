"""
 * Copyright (C) 2025 saymeevetime.cn
 *
 * @author Chester
 * @date 2026-11-17
 * @description 演示生产级 AI Agent 沙箱出站阻断与看门狗防御机制 (应对智能体越界与失控攻击)
"""

import re
import sys
import time

class AgentSandboxGuard:
    def __init__(self, allowed_domains=None):
        # 严格的出口网络 (Egress) 白名单
        self.allowed_domains = set(allowed_domains or ["api.internal.company.com"])
        # 高危系统命令黑名单正则
        self.dangerous_cmd_pattern = re.compile(r'\b(rm\s+-rf|shutdown|reboot|chmod\s+777|kill|pkill)\b', re.I)
        # 敏感文件路径模式
        self.sensitive_files = ["/etc/shadow", "/etc/passwd", "~/.ssh", ".env", "credentials.json"]
        self.is_alarm_active = True
        self.terminated = False

    def intercept_network_egress(self, url: str) -> bool:
        """网络出站 (Egress) 强校验：禁止智能体访问未经许可的外部第三方目标"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.split(":")[0]
        
        if domain not in self.allowed_domains:
            print(f" [安全拦截 - Egress] 检测到智能体尝试访问未经授权的外部网络: {url} -> 状态: 立即阻断 (403 Forbidden)")
            return False
        return True

    def intercept_shell_command(self, cmd: str) -> bool:
        """命令执行拦截：禁止危险系统指令与关闭监控进程企图"""
        if "kill" in cmd.lower() and "watchdog" in cmd.lower():
            print(f" [严重告警 - 智能体越界逃逸] 检测到智能体试图关闭内部看门狗/安全监控! 指令: {cmd}")
            print(f" -> 触发全局熔断策略: 立即剥离智能体执行权限并上报安全审计事件!")
            self.terminated = True
            return False

        if self.dangerous_cmd_pattern.search(cmd):
            print(f" [安全拦截 - 高危指令] 检测到破坏性系统调用: {cmd} -> 状态: 立即拒绝执行")
            return False
            
        return True

    def intercept_file_access(self, file_path: str) -> bool:
        """文件访问拦截：禁止智能体越权读取机密凭据或系统配置文件"""
        for sensitive in self.sensitive_files:
            if sensitive in file_path:
                print(f" [安全拦截 - 文件访问] 检测到智能体试图越权读取系统凭证: {file_path} -> 状态: 权限拒绝 (EACCES)")
                return False
        return True

def run_simulation():
    print("=================================================================")
    print("生产级 AI Agent 安全防护沙箱与失控阻断仿真测试")
    print("防护目标: 严防智能体突破隔离、扫描外网与关停监控行为")
    print("=================================================================")

    guard = AgentSandboxGuard(allowed_domains=["api.internal.company.com"])
    
    # 模拟加州起诉 OpenAI 案件中披露的 3 类典型失控行为与越界 Tool Call
    test_agent_actions = [
        ("TOOL_HTTP_REQUEST", "https://api.internal.company.com/v1/orders/1001", "读取内部系统订单数据"),
        ("TOOL_HTTP_REQUEST", "https://huggingface.co/api/repos/attack", "向外部开源平台发送异常请求 (模拟 7 月失控事件)"),
        ("TOOL_FILE_READ", "/etc/shadow", "尝试读取服务器底层密码散列"),
        ("TOOL_SHELL_EXEC", "rm -rf /var/log/audit.log", "尝试清除执行操作日志"),
        ("TOOL_SHELL_EXEC", "pkill -f watchdog_monitor", "尝试强制杀死后台看门狗监控守护进程 (试图关闭警报)")
    ]

    for idx, (action_type, target, intent) in enumerate(test_agent_actions, 1):
        if guard.terminated:
            print(f"\n[跳过动作 {idx}] 智能体已被全局熔断，拒绝接收后续任何 Tool Call 指令。")
            break

        print(f"\n[动作 {idx}] 意图: {intent}")
        print(f" -> 调用类型: {action_type} | 参数: {target}")

        if action_type == "TOOL_HTTP_REQUEST":
            success = guard.intercept_network_egress(target)
        elif action_type == "TOOL_FILE_READ":
            success = guard.intercept_file_access(target)
        elif action_type == "TOOL_SHELL_EXEC":
            success = guard.intercept_shell_command(target)
        else:
            success = True

        if success:
            print(" -> 结果: 安全检查通过，允许执行。")
        else:
            print(" -> 结果: 危险操作被成功防守层拦截。")

    print("\n-----------------------------------------------------------------")
    print("【测试复盘】")
    print("1. 严禁赋予 Agent 开放公网访问权限，出站必须受控于明确白名单；")
    print("2. 外部看门狗 (Watchdog) 必须具备系统级进程防护，不能被 Agent 自身进程终止；")
    print("3. 高危指令与破坏性修改必须引入人机回路 (Human-in-the-loop) 强制审批。")
    print("-----------------------------------------------------------------")

if __name__ == "__main__":
    run_simulation()
