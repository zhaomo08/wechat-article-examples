# 按话题分派人工事件

这是解释调度行为的独立自造示例，灵感来自 [DeepSeek 公开研究原型](https://github.com/deepseek-ai/dsh-superagent-prototype)。不是官方实现，不调用 DeepSeek 或其他模型，不访问 GitHub、飞书、账号或真实项目。

## 运行

Python 3.10+，仅标准库，无额外依赖。本次验证为 macOS、Python 3.12.3。

```bash
DEMO_DIR="$(mktemp -d)"
cd "$DEMO_DIR"
python3 /你的路径/wechat-article-examples/examples/2026-11-01/01-thread-routing/demo.py
```

只在当前临时目录创建 `demo.sqlite`。已有同名数据库时拒绝覆盖。真实输出见 `expected.txt`。

两个人工 PR 话题各有一个 asyncio 任务；同一话题的后续事件投给已有队列。Event 等待点验证前台分派结束时两个任务尚未完成。SQLite 主键记录事件 ID，正常完成后关闭并重新打开数据库，重复投递不会再次创建 Worker。

这里的 Worker 只是收集中文字符串。固定话题路由没有语义判断，`new_worker_routes` 不是模型调用数；`worker_results` 是本地收集结果数，不是外部发送量。`sleep(0)` 仅让出事件循环，没有用于计时或宣称性能提升。

## 没覆盖的情况

这是有限输入、单进程、无并发新消息的演示。它没有持久任务队列、租约、故障恢复、跨进程并发、背压、取消、授权判断或外部副作用回执。尤其若第一次执行中途崩溃，单靠事件 ID 去重无法恢复未完成工作。不要把正常完成后的重放测试当作 exactly-once 保证，也不要直接用于生产。

所有事件文字均为人工样本，无真实 PR 或业务数据。
