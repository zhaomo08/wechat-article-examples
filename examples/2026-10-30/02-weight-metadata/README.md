# 下载权重前，先统计官方文件清单

只读Hugging Face官方模型仓库的JSON元数据；不下载任何权重分片，不运行推理、不评测模型，也不估算实际显存需求。这里只汇总指定checkpoint分片的文件字节数，不包含tokenizer等附属文件。

环境：Python 3.12.3标准库，无第三方依赖、登录或付费服务。

默认离线读随附的2026-10-30公开元数据快照：

```bash
python3 inspect_weights.py
```

从固定revision重新联网读清单（最大1MB JSON；仍不下载权重）：

```bash
python3 inspect_weights.py --refresh
```

两条命令本次均实际运行，输出一致，见`expected.txt`。脚本核对分片编号是否连续、计数是否与文件名声明相符，避免漏页时误报完整大小。快照只含公开文件名与大小，不含模型权重和用户信息。

TB按`10**12`字节，TiB按`2**40`字节。文件大小不等于运行内存或显存，不能据此直接选机器。本文所核验的版本固定为`f12dabdc0c1e99e7f7924461a6f308859b05af4d`，其他量化版应单独统计。

来源：[官方模型仓库](https://huggingface.co/mistralai/Mistral-Large-4-1T-A52B)、[固定revision清单](https://huggingface.co/api/models/mistralai/Mistral-Large-4-1T-A52B/tree/f12dabdc0c1e99e7f7924461a6f308859b05af4d?recursive=false&expand=false)。
