# 多租户 AI 智能体会话隔离与并发防串线机制

## 痛点与背景

在生产环境中开发多租户 AI 智能体（如企业多租户客服、Copilot 插件、自动化工作流）时，最致命的严重安全事故莫过于**跨租户会话串线（Cross-session Pollution）**——张三在咨询隐私问题，大模型却由于共享缓冲区未清理，把李四的银行存款或订单信息拼进了张三的 Prompt 中（如近期 Meta Muse 智能体曝出的会话串号缺陷）。

## 核心漏洞根源

1. **单例模式滥用**：在后端微服务或 LangChain / 框架中，错误地将 `ConversationBufferMemory` 或状态机注册为单例 Bean / 全局变量。
2. **协程/线程池上下文残留**：在 Python `asyncio` 中未正确重置 `contextvars.ContextVar`，或在 Java 线程池中复用带有残留 `ThreadLocal` 的线程。
3. **RAG 向量库共享漏过滤**：多租户共享一个 Vector Collection 时，检索查询遗漏了 `tenant_id` 过滤条件。

## 运行基准仿真

```bash
python3 agent_session_isolation_demo.py
```

## 实测对比输出

- **实验 1（单例共享模式）**：Alice 发起育儿咨询，Bob 并发发起银行存款查询，Alice 的 Prompt 上下文直接混入 Bob 的私密资产数据，发生严重安全泄漏。
- **实验 2（零共享模式）**：通过 ContextVar 生命周期严格重置与独立 Session 容器，即便高并发交错，租户数据 100% 物理隔离。
- **实验 3（越界防御断言）**：非授权上下文试图读写其他租户数据时，直接触发 `PermissionError` 硬阻断。
