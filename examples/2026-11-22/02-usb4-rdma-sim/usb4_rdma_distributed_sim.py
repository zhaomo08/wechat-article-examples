#!/usr/bin/env python3
"""
USB4 RDMA vs Ethernet TCP/IP Distributed Inference Latency Simulator
Models Tensor Parallelism (TP) All-Reduce communication across 3 clustered PCs.
Demonstrates why microsecond-level latency is the lifeblood of distributed local LLM inference.
"""

import time
import math

def simulate_inference(protocol_name: str, rtt_us: float, bandwidth_gbps: float, num_layers: int = 80, num_tokens: int = 50):
    # Model: 70B model split across 3 nodes (Tensor Parallel = 3)
    # Each transformer layer performs 2 All-Reduce syncs (Self-Attention + MLP)
    # Message payload per All-Reduce: 32 KB (hidden_dim=8192, 16-bit float tensor slice)
    msg_size_bytes = 32 * 1024
    syncs_per_layer = 2
    total_syncs_per_token = num_layers * syncs_per_layer  # 160 syncs / token

    # Serialization & transfer time per sync
    transfer_time_us = (msg_size_bytes * 8) / (bandwidth_gbps * 1e9) * 1e6
    one_way_latency_us = (rtt_us / 2.0) + transfer_time_us
    # Ring All-Reduce communication overhead per sync: 2 * (N - 1) transfers for N=3 nodes -> 4 transfers
    allreduce_comm_time_per_sync_us = 4 * one_way_latency_us

    # Total communication time per token
    comm_time_per_token_ms = (total_syncs_per_token * allreduce_comm_time_per_sync_us) / 1000.0

    # Fixed GPU computation time per token across 3 nodes (e.g. AMD Ryzen AI Max 395 @ 4-bit)
    compute_time_per_token_ms = 22.0  # ms pure compute

    total_latency_per_token_ms = compute_time_per_token_ms + comm_time_per_token_ms
    tokens_per_sec = 1000.0 / total_latency_per_token_ms

    return {
        "protocol": protocol_name,
        "rtt_us": rtt_us,
        "bandwidth_gbps": bandwidth_gbps,
        "comm_per_token_ms": comm_time_per_token_ms,
        "compute_per_token_ms": compute_time_per_token_ms,
        "total_latency_ms": total_latency_per_token_ms,
        "tokens_per_sec": tokens_per_sec,
        "total_time_s": (total_latency_per_token_ms * num_tokens) / 1000.0
    }

def main():
    print("=" * 76)
    print("Distributed LLM Inference Benchmark: USB4 RDMA vs Traditional Ethernet")
    print("Cluster: 3x AI PC Nodes | Model: 70B Parameter | Layer Count: 80")
    print("Workload: Tensor Parallelism (TP=3) All-Reduce sync (160 syncs/token)")
    print("=" * 76)

    cases = [
        ("Gigabit Ethernet (1Gbps TCP/IP)", 280.0, 1.0),
        ("10GbE Switch (10Gbps TCP/IP)", 160.0, 10.0),
        ("Ethernet over USB4 (UDP Packets)", 125.0, 20.0),
        ("Microsoft RDMA over USB4 (DMA Rings)", 32.0, 40.0),
    ]

    results = []
    for name, rtt, bw in cases:
        res = simulate_inference(name, rtt, bw)
        results.append(res)

    print(f"{'Protocol / Network Stack':<38} | {'RTT (us)':<8} | {'Comm (ms)':<9} | {'Token Latency':<13} | {'Throughput'}")
    print("-" * 88)
    for r in results:
        print(f"{r['protocol']:<38} | {r['rtt_us']:<8.1f} | {r['comm_per_token_ms']:<9.1f} | {r['total_latency_ms']:<7.1f} ms    | {r['tokens_per_sec']:<5.1f} tok/s")

    print("=" * 88)
    base = results[0]["total_latency_ms"]
    usb4_rdma = results[3]["total_latency_ms"]
    speedup = base / usb4_rdma
    print(f"\n[KEY INSIGHT]")
    print(f"* Traditional TCP/IP waste ~{results[0]['comm_per_token_ms']:.1f}ms per token just idling on kernel socket buffers!")
    print(f"* RDMA over USB4 cuts per-token communication to just {results[3]['comm_per_token_ms']:.1f}ms.")
    print(f"* Overall cluster speedup: {speedup:.1f}x faster inference ({results[3]['tokens_per_sec']:.1f} vs {results[0]['tokens_per_sec']:.1f} tok/s).")
    print(f"* Turns previously unusable daisy-chained mini PCs into a production-grade 18+ tok/s cluster!")

if __name__ == "__main__":
    main()
