"""
 * Copyright (C) 2025 saymeevetime.cn
 *
 * @author Chester
 * @date 2026-11-17
 * @description 演示大模型 Prompt Cache 前缀匹配原理与费用对比测试 (基于 Qwen4-Max / 标准 KV 缓存规则)
"""

import hashlib
import re

BASE_KNOWLEDGE = """
# 核心业务系统微服务架构与开发规范手册 v3.2
## 1. 领域架构与分库分表
- 用户中心 (user-center): 承载用户身份认证、OAuth2 授权令牌颁发、用户基础资料管理。用户表 t_user 采用 MySQL 8.0 InnoDB 存储，主键使用雪花算法生成的 64 位全局唯一 ID。
- 订单履约中心 (order-fulfillment): 承载下单、库存预占、支付回调流转、物流派发。核心订单表 t_order 按照 user_id 字段进行散列取模，路由到 16 个独立的数据库实例，单库 16 张物理子表，单表容量控制在 500 万行以内。
- 支付结算网关 (payment-gateway): 对接微信支付、支付宝、银联在线。所有资金变动操作必须满足强一致性事务，采用本地消息表 + 可靠消息最终一致性方案。

## 2. 接口幂等性与分布式锁规范
- 所有 POST/PUT 写操作接口必须在 HTTP Header 中携带 X-Idempotency-Key 幂等令牌。
- 幂等防重逻辑采用 Redis setnx 原子指令：以 `idemp:{biz}:{key}` 为键，设置 24 小时过期时间。若返回 0 则直接阻断并返回上一次执行结果或 409 状态码。
- 分布式锁必须使用 Lua 脚本保证释放锁的原子性，防止锁被其他并发线程误删；锁过期时间默认 10 秒，长任务必须开启独立线程定时看门狗续期。

## 3. 熔断降级与慢 SQL 拦截准则
- 慢 SQL 阈值全局配置为 300ms。任何索引未命中的全表扫描 (type=ALL 且 rows > 10000) 将在测试环境流水线中直接报错拦截，禁止上线。
- 外部三方 RPC 调用超时时间必须显式配置：connectTimeout <= 1000ms, readTimeout <= 3000ms。核心链路熔断错误率阈值设定为 30%，熔断窗口期 10 秒。

## 4. 数据安全与合规审计
- 生产环境敏感数据禁止明文落盘。手机号必须展示为 138****1234，身份证号展示为前4后4。
- 数据库连接凭证、第三方 API Key 严禁硬编码在 Git 仓库内，统一通过 KMS 凭据管理中心动态拉取。
"""

class PromptCacheSimulator:
    def __init__(self, block_size=128):
        self.block_size = block_size
        self.cached_blocks = set()

    def tokenize(self, text: str):
        # 简单高效的模拟分词：英文单词、中文字符、符号
        return re.findall(r'[\u4e00-\u9fa5]|[A-Za-z0-9_]+|[^\s\w]', text)

    def process_request(self, full_prompt: str):
        tokens = self.tokenize(full_prompt)
        total_tokens = len(tokens)
        hit_tokens = 0
        
        num_blocks = total_tokens // self.block_size
        current_prefix_hash = ""
        is_hit = True
        
        # 计算当前请求中能命中的前缀块
        for i in range(num_blocks):
            block_slice = tokens[i * self.block_size : (i + 1) * self.block_size]
            block_str = "".join(block_slice)
            combined = current_prefix_hash + "|" + block_str
            current_prefix_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
            
            if is_hit and current_prefix_hash in self.cached_blocks:
                hit_tokens += self.block_size
            else:
                is_hit = False
                # 未命中的块在请求完成后写入 KV Cache 供后续请求复用
                self.cached_blocks.add(current_prefix_hash)
                
        miss_tokens = total_tokens - hit_tokens
        return total_tokens, hit_tokens, miss_tokens

def run_benchmark():
    print("=================================================================")
    print("大模型 Prompt Cache 前缀缓存命中机制与 API 账单对比测试")
    print("计费参考: Qwen4-Max / 主流长上下文大模型 API")
    print("- 普通未命中输入: 1.50 元 / 百万 Tokens")
    print("- 缓存命中输入:   0.50 元 / 百万 Tokens (降低 66.7%)")
    print("=================================================================")
    
    PRICE_MISS_PER_M = 1.50
    PRICE_HIT_PER_M = 0.50
    
    queries = [
        "1. 订单表物理分表之后，历史订单归档该怎么做？",
        "2. 支付回调接口收到重复的微信通知，如何做幂等？",
        "3. 用户手机号脱敏在批量导出时报错了怎么处理？",
        "4. 分布式锁看门狗在发生 GC 停顿时会不会导致死锁？",
        "5. 生产环境如何快速排查单库全表扫描的慢 SQL？"
    ]
    
    print("\n【实验组 A：反模式】—— 在 System Prompt 最开头插入动态时间戳与 RequestID")
    sim_bad = PromptCacheSimulator(block_size=128)
    bad_cost = 0.0
    bad_total = 0
    bad_hit = 0
    
    for idx, q in enumerate(queries):
        # 常见错误：把动态变量、毫秒时间戳塞在开头，导致前缀哈希链全部损坏
        dynamic_header = f"【系统环境】时间: 2026-11-17 10:3{idx}:{idx*11:02d} | TraceId: 0a93f{idx}c8912\n"
        prompt = dynamic_header + BASE_KNOWLEDGE + f"\n用户问题: {q}"
        
        total, hit, miss = sim_bad.process_request(prompt)
        cost = (miss * PRICE_MISS_PER_M + hit * PRICE_HIT_PER_M) / 1_000_000
        bad_cost += cost
        bad_total += total
        bad_hit += hit
        print(f"请求 {idx+1} -> 输入: {total} Tokens | 缓存命中: {hit} Tokens | 费用: ¥{cost:.6f}")
        
    print(f"-> 组 A 统计: 总 Tokens: {bad_total}, 命中: {bad_hit} (命中率: {bad_hit/bad_total*100:.1f}%), 总账单: ¥{bad_cost:.6f}")

    print("\n【实验组 B：最佳实践】—— 静态规范作为不可变前缀，动态变量放末尾")
    sim_good = PromptCacheSimulator(block_size=128)
    good_cost = 0.0
    good_total = 0
    good_hit = 0
    
    for idx, q in enumerate(queries):
        # 正确做法：长篇规范作为固定的第一段，动态内容全部挪到最后
        prompt = BASE_KNOWLEDGE + f"\n【请求参数】时间: 2026-11-17 10:3{idx}:{idx*11:02d} | TraceId: 0a93f{idx}c8912 | 用户问题: {q}"
        
        total, hit, miss = sim_good.process_request(prompt)
        cost = (miss * PRICE_MISS_PER_M + hit * PRICE_HIT_PER_M) / 1_000_000
        good_cost += cost
        good_total += total
        good_hit += hit
        print(f"请求 {idx+1} -> 输入: {total} Tokens | 缓存命中: {hit} Tokens | 费用: ¥{cost:.6f}")

    print(f"-> 组 B 统计: 总 Tokens: {good_total}, 命中: {good_hit} (命中率: {good_hit/good_total*100:.1f}%), 总账单: ¥{good_cost:.6f}")
    
    saving = (bad_cost - good_cost) / bad_cost * 100
    print("\n-----------------------------------------------------------------")
    print(f"【对比结果】")
    print(f"- 缓存命中率: 组 A ({bad_hit/bad_total*100:.1f}%) vs 组 B ({good_hit/good_total*100:.1f}%)")
    print(f"- 端到端总费用: 组 A (¥{bad_cost:.6f}) vs 组 B (¥{good_cost:.6f})")
    print(f"- 最终成本直接缩减: {saving:.1f}%")
    print("-----------------------------------------------------------------")

if __name__ == "__main__":
    run_benchmark()
