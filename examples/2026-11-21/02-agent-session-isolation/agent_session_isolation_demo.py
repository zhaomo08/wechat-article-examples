#!/usr/bin/env python3
"""
多租户 AI 智能体会话隔离与并发上下文防污染仿真基准测试
复现高并发下因为“全局单例 Memory / 协程未重置 ContextVar / 共享长连接”导致的会话串号泄漏，
并对比“零共享（Zero-Share）状态容器与硬隔离断言”的防御效果。
"""

import asyncio
import contextvars
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

# -------------------------------------------------------------
# 场景 1：危险模式 —— 伪隔离（依赖单例共享或未安全重置的全局上下文）
# -------------------------------------------------------------

class FlawedGlobalSessionManager:
    """常见踩坑模式：在微服务中把 Session / Memory 做成了单例或全局缓存"""
    def __init__(self):
        # 错误地在单例中维护共享对话缓冲区
        self._shared_buffer: List[Dict[str, str]] = []
        self._last_active_user: str = "anonymous"

    def append_message(self, user_id: str, role: str, content: str):
        self._last_active_user = user_id
        self._shared_buffer.append({"user": user_id, "role": role, "content": content})

    def get_context_for_prompt(self, user_id: str) -> str:
        # 并发交错时，容易直接取到共享缓冲区里其他租户的数据！
        # 很多新手只截取最近 N 条，直接忽略了 tenant 校验
        recent = self._shared_buffer[-3:]
        return " | ".join(f"[{item['user']}]: {item['content']}" for item in recent)

# -------------------------------------------------------------
# 场景 2：安全模式 —— 严格零共享与租户级强隔离容器
# -------------------------------------------------------------

# 使用安全作用域的 ContextVar
tenant_context_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

@dataclass
class SafeIsolatedSession:
    tenant_id: str
    session_id: str
    history: List[Dict[str, str]] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        # 强制断言当前执行上下文的租户 ID 一致，否则拒绝写入
        current_tenant = tenant_context_var.get()
        if current_tenant != self.tenant_id:
            raise PermissionError(f"CRITICAL: 租户上下文越界！当前上下文 {current_tenant} 试图写入租户 {self.tenant_id} 的会话！")
        self.history.append({"role": role, "content": content})

    def build_prompt_context(self) -> str:
        current_tenant = tenant_context_var.get()
        if current_tenant != self.tenant_id:
            raise PermissionError(f"CRITICAL: 租户上下文越界！当前上下文 {current_tenant} 试图读取租户 {self.tenant_id} 的数据！")
        return " | ".join(f"{h['role']}: {h['content']}" for h in self.history[-3:])


# -------------------------------------------------------------
# 并发仿真运行
# -------------------------------------------------------------

flawed_manager = FlawedGlobalSessionManager()

async def simulate_flawed_user_request(user_id: str, secret_data: str, delay: float):
    """模拟并发下请求交错执行"""
    # 步骤 1：写入用户私密提问
    flawed_manager.append_message(user_id, "user", f"我的私密数据是: {secret_data}")
    # 模拟网络 IO 或 LLM 调用耗时
    await asyncio.sleep(delay)
    # 步骤 2：生成 Prompt 并返回
    prompt_ctx = flawed_manager.get_context_for_prompt(user_id)
    return prompt_ctx

async def simulate_safe_user_request(tenant_id: str, secret_data: str, delay: float, session_store: Dict[str, SafeIsolatedSession]):
    """模拟安全模式下的租户隔离请求"""
    # 1. 中间件设置租户上下文
    token_tenant = tenant_context_var.set(tenant_id)
    token_req = request_id_var.set(f"req_{tenant_id}_{int(time.time()*1000)}")

    try:
        session = session_store[tenant_id]
        session.add_message("user", f"我的私密数据是: {secret_data}")
        await asyncio.sleep(delay)
        prompt_ctx = session.build_prompt_context()
        return prompt_ctx
    finally:
        # 请求生命周期结束强制清理重置 ContextVar，杜绝协程复用污染
        tenant_context_var.reset(token_tenant)
        request_id_var.reset(token_req)

async def main():
    print("=" * 75)
    print("多租户 AI 智能体会话隔离与并发防串线机制 - 基准对比测试")
    print("=" * 75)

    # 1. 运行有缺陷的共享模式
    print("\n[实验 1] 常见单例/全局状态下的并发串号复现:")
    print("  * 模拟并发：用户 Alice (查询育儿) 与用户 Bob (查询私密银行存款 89,450 元) 同时发起请求")
    
    task_alice = asyncio.create_task(simulate_flawed_user_request("Alice", "宝宝最近夜醒频繁怎么处理？", 0.05))
    task_bob = asyncio.create_task(simulate_flawed_user_request("Bob", "Capital One 账户可用余额 89,450 USD", 0.01))
    
    ctx_bob, ctx_alice = await asyncio.gather(task_bob, task_alice)
    
    print(f"  * [用户 Bob 获取的 Prompt 上下文]:\n    --> {ctx_bob}")
    print(f"  * [用户 Alice 获取的 Prompt 上下文]:\n    --> {ctx_alice}")
    
    is_leaked = "Bob" in ctx_alice or "89,450" in ctx_alice
    if is_leaked:
        print("  \033[91m[! 严重安全事故 !] Alice 的 Prompt 上下文混入了 Bob 的私密银行存款信息！（典型串线泄漏）\033[0m")

    # 2. 运行安全零共享模式
    print("\n" + "-" * 75)
    print("[实验 2] 采用 ContextVar 生命周期绑定 + 独立 Session 容器的防御效果:")
    
    sessions = {
        "Alice": SafeIsolatedSession(tenant_id="Alice", session_id="sess_001"),
        "Bob": SafeIsolatedSession(tenant_id="Bob", session_id="sess_002")
    }
    
    safe_alice = asyncio.create_task(simulate_safe_user_request("Alice", "宝宝最近夜醒频繁怎么处理？", 0.05, sessions))
    safe_bob = asyncio.create_task(simulate_safe_user_request("Bob", "Capital One 账户可用余额 89,450 USD", 0.01, sessions))
    
    safe_ctx_bob, safe_ctx_alice = await asyncio.gather(safe_bob, safe_alice)
    
    print(f"  * [安全隔离 - Bob 上下文]  : {safe_ctx_bob}")
    print(f"  * [安全隔离 - Alice 上下文]: {safe_ctx_alice}")
    
    safe_check = "Bob" not in safe_ctx_alice and "89,450" not in safe_ctx_alice
    if safe_check:
        print("  \033[92m[✓ 隔离验证通过] 无论并发请求如何交错交叠，租户上下文严格物理隔离，零数据泄漏！\033[0m")

    # 3. 故意测试越界防御断言
    print("\n" + "-" * 75)
    print("[实验 3] 模拟恶意/串号越界写入时的防御断言拦截:")
    token = tenant_context_var.set("Mallory_Attacker")
    try:
        # 攻击者试图直接调用 Alice 的会话对象
        sessions["Alice"].add_message("user", "恶意注入数据")
        print("  \033[91m[失败] 未拦截跨租户调用！\033[0m")
    except PermissionError as e:
        print(f"  \033[92m[✓ 拦截成功] 防御断言触发: {e}\033[0m")
    finally:
        tenant_context_var.reset(token)

    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(main())
