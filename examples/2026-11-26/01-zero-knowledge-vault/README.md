# 01-zero-knowledge-vault

> 公众号 2026-11-26 科技头条文章示例代码：深入拆解 1Password 零知识端到端加密与防脱裤实战。

## 简介

本项目模拟 1Password 核心安全架构：
1. **双密钥派生体系**：客户端本地生成 128 位随机 Secret Key，与用户 Master Password 经 PBKDF2-HMAC-SHA256 派生双密钥（AES 加密密钥 + HMAC 认证密钥）。
2. **服务端零知识**：Secret Key 仅存在于用户本地设备，服务端仅存储密文、Salt 和 MAC 认证标签。
3. **真实防脱裤验证**：模拟服务端数据库与私有源码被黑客全量窃取时，黑客即使猜中用户主密码，因缺少本地 Secret Key 依然遭遇 $2^{128}$ 密码学壁垒，彻底拦截非法解密。

## 快速运行

无任何第三方外部依赖（仅需 Python 3 + 系统内置 OpenSSL）：

```bash
python3 zero_knowledge_vault.py
```
