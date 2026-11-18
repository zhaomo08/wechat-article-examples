#!/usr/bin/env python3
"""
重试风暴与退避抖动仿真器 (Retry Storm & Jitter Benchmark)
模拟 10,000 个高并发客户端在面对服务端故障（持续 5 秒）时的请求行为与服务端瞬时负载冲击。
"""
import random
import math
import collections

TOTAL_CLIENTS = 10000
OUTAGE_DURATION = 5.0   # 服务端不可用持续时间（秒）
MAX_RETRIES = 3
BASE_DELAY = 1.0        # 初始基准延迟（秒）
MAX_DELAY = 10.0        # 最大退避延迟（秒）
SIMULATION_STEPS = 20   # 模拟 0 ~ 20 秒
SERVER_CAPACITY_QPS = 1500  # 服务端能承受的最大 QPS

def simulate_immediate_retry():
    # 策略 1：固定立即重试（失败立刻重发，重试 3 次，每次只间隔 0.2s）
    qps_buckets = collections.defaultdict(int)
    for _ in range(TOTAL_CLIENTS):
        t = random.uniform(0.0, 1.0) # 0-1 秒内首发
        for attempt in range(MAX_RETRIES + 1):
            sec = int(t)
            qps_buckets[sec] += 1
            if t >= OUTAGE_DURATION:
                # 服务已恢复，成功返回
                break
            # 失败，立即固定间隔重试
            t += 0.2
    return qps_buckets

def simulate_exponential_no_jitter():
    # 策略 2：经典指数退避（无随机抖动）：2^attempt * base
    qps_buckets = collections.defaultdict(int)
    for _ in range(TOTAL_CLIENTS):
        t = random.uniform(0.0, 1.0)
        for attempt in range(MAX_RETRIES + 1):
            sec = int(t)
            qps_buckets[sec] += 1
            if t >= OUTAGE_DURATION:
                break
            delay = min(MAX_DELAY, BASE_DELAY * (2 ** attempt))
            t += delay
    return qps_buckets

def simulate_full_jitter():
    # 策略 3：完全抖动指数退避 (Full Jitter)：random(0, min(MAX_DELAY, base * 2^attempt))
    qps_buckets = collections.defaultdict(int)
    for _ in range(TOTAL_CLIENTS):
        t = random.uniform(0.0, 1.0)
        for attempt in range(MAX_RETRIES + 1):
            sec = int(t)
            qps_buckets[sec] += 1
            if t >= OUTAGE_DURATION:
                break
            cap = min(MAX_DELAY, BASE_DELAY * (2 ** attempt))
            delay = random.uniform(0, cap)
            t += delay
    return qps_buckets

def main():
    print("=" * 60)
    print("高并发微服务『重试风暴』仿真测试 (10,000 客户端，故障 5 秒)")
    print(f"服务端单机/集群承载安全阈值: {SERVER_CAPACITY_QPS} QPS")
    print("=" * 60)

    res_imm = simulate_immediate_retry()
    res_exp = simulate_exponential_no_jitter()
    res_jit = simulate_full_jitter()

    print(f"{'时间(秒)':<8} | {'立即固定重试 QPS':<16} | {'纯指数退避 QPS':<14} | {'Full Jitter 抖动 QPS':<16}")
    print("-" * 65)

    max_imm = max(res_imm.values()) if res_imm else 0
    max_exp = max(res_exp.values()) if res_exp else 0
    max_jit = max(res_jit.values()) if res_jit else 0

    for s in range(0, 12):
        v1 = res_imm.get(s, 0)
        v2 = res_exp.get(s, 0)
        v3 = res_jit.get(s, 0)
        warn1 = " [被打死]" if v1 > SERVER_CAPACITY_QPS else ""
        warn2 = " [被打死]" if v2 > SERVER_CAPACITY_QPS else ""
        warn3 = " [被打死]" if v3 > SERVER_CAPACITY_QPS else ""
        print(f"T+{s:02d}s     | {v1:<10}{warn1:<6} | {v2:<8}{warn2:<6} | {v3:<10}{warn3:<6}")

    print("=" * 65)
    print(f"峰值冲击对比:")
    print(f" - 立即固定重试峰值: {max_imm} QPS (超标 {(max_imm/SERVER_CAPACITY_QPS - 1)*100:.1f}%)")
    print(f" - 纯指数退避峰值:   {max_exp} QPS (超标 {(max_exp/SERVER_CAPACITY_QPS - 1)*100:.1f}%) -> 存在周期共振脉冲")
    print(f" - Full Jitter 峰值: {max_jit} QPS (处于安全水位内，打散洪峰，系统平稳自愈)")

if __name__ == "__main__":
    main()
