# 大模型 Prompt Cache 前缀缓存命中基准测试

本项目模拟阿里云 Qwen4-Max 及主流长上下文大模型（如 DeepSeek、Claude、OpenAI）的 Prompt Cache（上下文缓存）机制。

## 运行环境
- macOS / Linux
- Python 3.8+（无需任何第三方依赖，仅使用标准库）

## 运行方式
```bash
python3 cache_benchmark.py
```

## 测试逻辑
1. **实验组 A（反模式）**：在 System Prompt 最前面动态拼接请求 ID 和当前时间戳。导致前缀哈希每次完全不同，缓存命中率为 0%，每次请求均全额计费。
2. **实验组 B（推荐实践）**：将静态长规范/知识库作为绝对不可变前缀，动态时间戳和用户问题追加在末尾。从第 2 次请求起精准命中 640 Tokens 缓存，单次请求成本直降 60%，端到端账单缩减近半。

真实测试输出见 [output.txt](output.txt)。
