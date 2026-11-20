# 谷歌 Harness 自我演进与模块化约束基准测试 (2026-11-20)

本示例代码复现谷歌研究团队 2026 年 11 月 17 日发表的学术论文《Harnesses That Improve Themselves》（《能够自我改进的 Harness》）的核心实验。

## 核心技术背景

在构建自主编程智能体（Coding Agent）时，许多工程团队在遭遇任务失败时，第一反应往往是怪模型“智商不够”，随后开始在 System Prompt 中堆砌成百上千字的行为规范。

谷歌的研究通过 40 道 SWE-bench Lite 独立任务证明：
1. **仅堆砌提示词规则（Prompt-Only Bloat）**：成功率不仅没有提升，反而从 5.0% 跌落至 2.5%。提示词过长造成注意力稀释与幻觉。
2. **整体重写 Harness（Monolithic Rewrite）**：成功率达 42.5%，但单任务 Token 消耗高达近 40 万 Token，产生严重的死循环与开销膨胀。
3. **模块化工程脚手架（Modular Engineered Harness）**：将 Harness 拆解为上下文状态隔离、智能体控制器（死循环熔断）、工具调用接口（结构化堆栈）和验证门禁（强制自动化测试套件断言）四大模块，成功率从 5.0% 飙升至 40.0%（提升 8 倍），Token 消耗降低近 90%。

## 快速运行

```bash
python3 agent_harness_benchmark.py
```

## 运行输出样例

```text
==================================================================================
Google Research Benchmark: Harnesses That Improve Themselves (SWE-bench Lite)
Evaluating Agent Architectures Across 40 Real-World Software Engineering Tasks
==================================================================================
Harness Architecture           | Success Rate     | Avg Tokens/Task  | Avg Loops 
----------------------------------------------------------------------------------
1. Initial Minimal (142 lines) |   5.0%            |          850 tok |   1.0 loops
2. Prompt-Only Rules Bloat     |   2.5%            |       10,412 tok |   3.0 loops
3. Monolithic Rewrite (Unchecked) |  42.5% (8x Boost!) |      390,297 tok |  11.2 loops
4. Modular Engineered Harness  |  40.0% (8x Boost!) |       40,389 tok |   4.3 loops
==================================================================================
```
