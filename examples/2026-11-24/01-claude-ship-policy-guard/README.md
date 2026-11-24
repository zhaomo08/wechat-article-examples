# Claude Ship 自动化 PR 审核策略守卫原型 (Policy-as-Code)

针对 Anthropic 发布的全新全自动代码审查与合并工具 **Claude Ship (beta)**，构建的声明式 PR 审批与合并安全策略守卫原型。

## 场景痛点
AI 编程工具大幅推高了代码产出速度，导致 GitHub PR 堆积。直接开启 AI 自动 Approve 会面临“同源盲区”——AI 无法可靠识别深层并发事务、越权漏洞与数据库迁移隐患。

## 运行方式
```bash
python3 claude_ship_policy_guard.py
```

## 核心机制
1. **分级放行门禁 (Tiered Approvals)**：低风险变更（单测、文档、样式、类型定义）在行数受控、CI 全绿前提下允许 AI 自动 Approve；
2. **敏感路径熔断 (Restricted Path Guard)**：触碰鉴权 (`src/auth/`)、支付 (`src/payment/`)、数据库变更 (`migrations/*.sql`) 或 CI 流水线时，强制阻断自动审批，上锁转人工高级架构师签批。
