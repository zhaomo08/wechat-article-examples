# 微软 RDMA over USB4 分布式大模型张量并行 (TP) 通信基准仿真

本示例量化了在 3 台分布式 PC 运行 70B 大模型时，不同互联协议（传统以太网 TCP/IP、万兆交换机、USB4 UDP、微软 RDMA over USB4）在层间张量 All-Reduce 同步时的真实通信耗时与生成吞吐。

## 实验配置
- **集群架构**：3 节点 PC（如 AMD Ryzen AI Max 395 或 Intel Core Ultra Series 3）
- **模型规格**：70B 参数量，80 层 Transformer
- **并行模式**：张量并行 TP=3，每层 2 次 All-Reduce（Self-Attention + MLP），单 Token 需经历 160 次跨机同步
- **单次同步载荷**：32 KB 激活切片（hidden_dim=8192, FP16）

## 运行方式
```bash
python3 usb4_rdma_distributed_sim.py
```

## 运行输出
```text
============================================================================
Distributed LLM Inference Benchmark: USB4 RDMA vs Traditional Ethernet
Cluster: 3x AI PC Nodes | Model: 70B Parameter | Layer Count: 80
Workload: Tensor Parallelism (TP=3) All-Reduce sync (160 syncs/token)
============================================================================
Protocol / Network Stack               | RTT (us) | Comm (ms) | Token Latency | Throughput
----------------------------------------------------------------------------------------
Gigabit Ethernet (1Gbps TCP/IP)        | 280.0    | 257.4     | 279.4   ms    | 3.6   tok/s
10GbE Switch (10Gbps TCP/IP)           | 160.0    | 68.0      | 90.0    ms    | 11.1  tok/s
Ethernet over USB4 (UDP Packets)       | 125.0    | 48.4      | 70.4    ms    | 14.2  tok/s
Microsoft RDMA over USB4 (DMA Rings)   | 32.0     | 14.4      | 36.4    ms    | 27.4  tok/s
========================================================================================

[KEY INSIGHT]
* Traditional TCP/IP waste ~257.4ms per token just idling on kernel socket buffers!
* RDMA over USB4 cuts per-token communication to just 14.4ms.
* Overall cluster speedup: 7.7x faster inference (27.4 vs 3.6 tok/s).
* Turns previously unusable daisy-chained mini PCs into a production-grade 18+ tok/s cluster!
```
