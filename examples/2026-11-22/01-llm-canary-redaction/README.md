# LLM 出网脱敏与金丝雀探针 (Canary Token) 泄露检测示例

本示例用于验证企业或开发者在调用外部第三方 LLM API 时，如何通过轻量级安全代理阻断凭证泄露，并主动追踪离线数据回流与第三方非法访问。

## 核心实现
1. **敏感凭据与 PII 正则掩码**：在 Prompt 离开内网前，将数据库密码、API Key、内网 IP、手机号等敏感信息替换为唯一哈希占位符。
2. **金丝雀探针（Canary Token）注入**：为每个出网请求注入唯一专属探针 URL，并在内存/Redis 注册生命周期。
3. **第三方抓取告警捕获**：模拟外部爬虫在 40~130 小时后触发探针 URL，网关即时报警并提取来源 IP/UA。
4. **安全可信环境反向解密**：模型返回结果后，在网关层将占位符还原为原始实体，业务层无感知。

## 运行方式
```bash
python3 canary_redaction_proxy.py
```

## 运行输出
```text
========================================================================
LLM Outbound Security Proxy: Redaction & Canary Leak Detection Demo
========================================================================

[Step 1] Developer sends raw prompt with sensitive internal credentials:
------------------------------------------------------------------------
排查线上报警：支付网关与数据库连接超时。
配置详情：
  - 数据库地址: 192.168.1.188:3306
  - 账号: root, password: SuperSecretP@ssw0rd!2026
  - 第三方通道商 API Key: sk-live-982187349128471204918234
  - 应急值班人手机: 13812345678
请帮我分析连接池参数与排查思路。

[Step 2] Outbound Security Gateway Redacts Data & Injects Canary Token:
------------------------------------------------------------------------
排查线上报警：支付网关与数据库连接超时。
配置详情：
  - 数据库地址: <REDACTED_INTERNAL_IP_e616d044>:3306
  - 账号: root, <REDACTED_DB_PASS_ee83665b>
  - 第三方通道商 API Key: sk-live-982187349128471204918234
  - 应急值班人手机: <REDACTED_PHONE_4c0115d3>
请帮我分析连接池参数与排查思路。

<!-- Reference Audit Checksum: https://canary.internal.corp/probe/34d11c3981f6b346.png -->

[Step 3] Model Provider receives sanitized payload and generates response:
建议排查步骤：
1. 确认 <REDACTED_IP_6ec0fa72> 机器上的 3306 端口 iptables 防火墙是否放行；
2. 密码 <REDACTED_DB_PASS_6cd75121> 建议配置进 KMS 密钥管理系统，避免明文；
3. 检查 HikariCP 连接池 maximumPoolSize 与 idleTimeout 设置。

[Step 4] Gateway securely restores placeholders before handing back to developer:
------------------------------------------------------------------------
建议排查步骤：
1. 确认 <REDACTED_IP_6ec0fa72> 机器上的 3306 端口 iptables 防火墙是否放行；
2. 密码 <REDACTED_DB_PASS_6cd75121> 建议配置进 KMS 密钥管理系统，避免明文；
3. 检查 HikariCP 连接池 maximumPoolSize 与 idleTimeout 设置。

[Step 5] Simulating delayed leak (~72 hours later, external bot hits Canary URL):
------------------------------------------------------------------------
[CRITICAL LEAK ALERT] Canary Token 34d11c3981f6b346 triggered!
  - Original Model: minimax/text-01-turbo
  - Request ID: 283a876b
  - Access Time Delay: ~72.0 hours after completion
  - External IP: 198.51.100.74 (Unknown Cloud Scraper) | UA: Mozilla/5.0 (compatible; DataminingCrawler/3.2)
  -> EVIDENCE: Prompt payload was retained and accessed by an unauthorized 3rd party!

[Audit Result] ZERO real credentials leaked to external crawler!
========================================================================
```
