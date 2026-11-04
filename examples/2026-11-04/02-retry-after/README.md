# 本机HTTP重试小实验

Python3标准库，无第三方依赖。启动仅监听127.0.0.1的临时HTTP服务，测试GET请求：两次503后恢复、Retry-After超过等待预算、401不重试。没有连接DeepSeek或任何外部模型，也不是其故障复现、性能测试或官方SDK。

在这个目录运行：

```bash
python3 demo.py
```

也可以在临时目录执行并记录真实计时：

```bash
DEMO_DIR="$(mktemp -d)"
cp demo.py "$DEMO_DIR/"
cd "$DEMO_DIR"
python3 demo.py --output result.json
```

输出见expected.txt。result.json保留本机真实的请求间隔，不作为生产性能承诺。脚本退出时关闭服务；输出JSON存在时拒绝覆盖。

重试次数包含第一次尝试。Retry-After支持非负整数秒和HTTP日期，预算不足时停止，不把服务端要求的等待偷偷缩短。没有Retry-After时使用短指数退避；本例没有添加随机抖动，生产中的并发客户端还应考虑抖动和SDK已有重试行为。这里的预算是尝试前/等待前检查，配合单次socket超时，不是严格硬实时截止；仅限本机GET，不适合直接复制成生成、扣费或其他有副作用操作的自动重试器。

依据：[RFC9110 Retry-After](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3)、[Python urllib.request](https://docs.python.org/3/library/urllib.request.html)。
