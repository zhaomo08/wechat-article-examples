#!/usr/bin/env python3
"""
Zero-Knowledge Vault Prototype (1Password Architecture Simulation)
模拟 1Password 端到端零知识双密钥架构与服务端防脱裤验证

核心流程：
1. 客户端本地生成 128-bit Secret Key，结合主密码通过 PBKDF2-HMAC-SHA256 派生双密钥（加密密钥 + 验签密钥）
2. 客户端在本地执行 Encrypt-then-MAC 加密，将密文与元数据上传至服务端
3. 模拟服务端源码泄露与数据库被“脱裤”：黑客拥有源码和数据库，但因缺失客户端本地 128-bit Secret Key，遭遇 2^128 暴力破解壁垒
4. 真实客户端使用完整凭据在本地成功解密恢复数据
"""

import os
import sys
import json
import base64
import secrets
import hashlib
import hmac
import subprocess

def generate_secret_key() -> str:
    """生成类似 1Password 风格的 128 位随机 Secret Key (A3-XXXX-XXXX-XXXX-XXXX)"""
    raw_bytes = secrets.token_bytes(16)
    b32 = base64.b32encode(raw_bytes).decode('utf-8').rstrip('=')
    return f"A3-{b32[0:4]}-{b32[4:8]}-{b32[8:12]}-{b32[12:16]}"

def derive_keys(master_password: str, secret_key: str, salt: bytes):
    """
    两阶段派生双密钥：
    第 1 阶段：主密码 + Salt 经由 100,000 次 PBKDF2-HMAC-SHA256 得到 intermediate_key
    第 2 阶段：结合本地独占的 Secret Key 做 HKDF 提取，派生出 encryption_key (AES-256) 和 mac_key (HMAC-SHA256)
    """
    # 阶段 1：密码哈希强化
    pwd_bytes = master_password.encode('utf-8')
    intermediate_key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt, iterations=100_000, dklen=32)
    
    # 阶段 2：混合本地 Secret Key (双因子密钥融合)
    sk_bytes = secret_key.strip().replace("-", "").encode('utf-8')
    prk = hmac.new(sk_bytes, intermediate_key, hashlib.sha256).digest()
    
    # 派生两个独立 256 位密钥
    enc_key = hmac.new(prk, b"encryption-key-v1", hashlib.sha256).digest()
    mac_key = hmac.new(prk, b"mac-key-v1", hashlib.sha256).digest()
    return enc_key, mac_key

def aes_encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    """调用 OpenSSL CLI 执行 AES-256-CBC 加密"""
    iv = os.urandom(16)
    key_hex = key.hex()
    iv_hex = iv.hex()
    proc = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-K", key_hex, "-iv", iv_hex],
        input=plaintext,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )
    return iv, proc.stdout

def aes_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """调用 OpenSSL CLI 执行 AES-256-CBC 解密"""
    key_hex = key.hex()
    iv_hex = iv.hex()
    proc = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-K", key_hex, "-iv", iv_hex],
        input=ciphertext,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        raise ValueError("Decryption failed or invalid padding")
    return proc.stdout

class ZeroKnowledgeClient:
    def __init__(self, email: str, master_password: str, secret_key: str = None):
        self.email = email
        self.master_password = master_password
        self.secret_key = secret_key or generate_secret_key()

    def encrypt_vault(self, vault_data: dict, salt: bytes) -> dict:
        enc_key, mac_key = derive_keys(self.master_password, self.secret_key, salt)
        data_bytes = json.dumps(vault_data, ensure_ascii=False).encode('utf-8')
        iv, ciphertext = aes_encrypt(enc_key, data_bytes)
        
        # Encrypt-then-MAC
        tag = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()
        
        return {
            "email": self.email,
            "iv": base64.b64encode(iv).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "mac": base64.b64encode(tag).decode('utf-8')
        }

    def decrypt_vault(self, encrypted_payload: dict, salt: bytes) -> dict:
        enc_key, mac_key = derive_keys(self.master_password, self.secret_key, salt)
        iv = base64.b64decode(encrypted_payload["iv"])
        ciphertext = base64.b64decode(encrypted_payload["ciphertext"])
        expected_mac = base64.b64decode(encrypted_payload["mac"])
        
        # 1. 验证 MAC
        calculated_mac = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(calculated_mac, expected_mac):
            raise PermissionError("MAC verification failed! Data tampered or incorrect keys.")
        
        # 2. 解密
        plaintext = aes_decrypt(enc_key, iv, ciphertext)
        return json.loads(plaintext.decode('utf-8'))

class UntrustedServerDatabase:
    """模拟云端服务端的数据库存储（服务端对用户数据零知识）"""
    def __init__(self):
        self.users = {}      # email -> { salt }
        self.vaults = {}     # email -> encrypted_payload

    def register_user(self, email: str) -> bytes:
        salt = os.urandom(16)
        self.users[email] = {"salt": base64.b64encode(salt).decode('utf-8')}
        return salt

    def save_vault(self, email: str, encrypted_payload: dict):
        self.vaults[email] = encrypted_payload

    def dump_database(self) -> dict:
        """模拟黑客脱裤导出的全量数据库内容"""
        return {
            "users_table": self.users,
            "vaults_table": self.vaults
        }

def run_simulation():
    print("=" * 70)
    print("   1Password 零知识端到端双密钥架构与防脱裤真实模拟")
    print("=" * 70)
    
    server_db = UntrustedServerDatabase()
    
    # 1. 用户注册与客户端凭证生成
    email = "developer@enterprise.internal"
    user_password = "MyComplexPassword2026!#"
    client = ZeroKnowledgeClient(email=email, master_password=user_password)
    
    print("\n[Step 1] 客户端本地生成用户安全凭据：")
    print(f"  - 用户账号: {client.email}")
    print(f"  - 用户主密码 (本地保管): {client.master_password}")
    print(f"  - 本地随机 128-bit Secret Key: {client.secret_key}")
    print("  * 核心设计原则：Secret Key 仅保存在客户端本地 Emergency Kit，绝不上报服务端！")
    
    # 服务端生成公用 Salt
    salt = server_db.register_user(email)
    
    # 2. 客户端在本地加密核心企业敏感资产
    sensitive_vault = {
        "production_db": {
            "host": "rds-prod-primary.internal.db",
            "user": "db_superadmin",
            "password": "pROD_DB_SECRET_KEY_9981!!"
        },
        "stripe_api_key": "mock_payment_api_key_sample_test_998811",
        "aws_root_access": {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        }
    }
    
    print("\n[Step 2] 客户端本地执行零知识加密并上传密文：")
    encrypted_payload = client.encrypt_vault(sensitive_vault, salt)
    server_db.save_vault(email, encrypted_payload)
    print(f"  - 上传密文长度: {len(encrypted_payload['ciphertext'])} chars")
    print(f"  - 数据认证 MAC: {encrypted_payload['mac'][:20]}...")
    print("  * 服务端仅收到密文与认证标签，完全不知晓明文内容与 Secret Key。")
    
    # 3. 模拟安全事件：员工 GitHub 账号被黑，源码被窃，服务端数据库被“脱裤”
    print("\n" + "!" * 70)
    print("[Step 3] 模拟安全事件：黑客攻入 CI/CD 与服务端，全量导出数据库！")
    print("!" * 70)
    
    leaked_dump = server_db.dump_database()
    print("黑客在脱裤数据库中获取到的全部数据清单：")
    print(json.dumps(leaked_dump, indent=2, ensure_ascii=False))
    
    # 4. 黑客尝试攻击解密
    print("\n[Step 4] 黑客拿到全套源码与脱裤数据库，尝试破解 Vault 密码库：")
    print("  - 黑客假定通过社工猜出了用户的主密码: 'MyComplexPassword2026!#'")
    print("  - 但是：黑客在数据库和源码中根本找不到用户的 128-bit Secret Key！")
    
    hacker_fake_secret_key = "A3-AAAA-BBBB-CCCC-DDDD"
    print(f"  - 黑客尝试随机伪造 Secret Key: {hacker_fake_secret_key}")
    
    hacker_client = ZeroKnowledgeClient(
        email=email,
        master_password=user_password,
        secret_key=hacker_fake_secret_key
    )
    
    try:
        hacker_client.decrypt_vault(leaked_dump["vaults_table"][email], salt)
        print("  [CRITICAL ERROR] 黑客意外解密成功！")
    except Exception as e:
        print(f"  - 解密结果: 失败！拦截原因: {e}")
        print("  - 密码学防线分析：")
        print("    即便黑客拥有主密码、全套后端源码和数据库密文，缺少本地 128 位 Secret Key，")
        print("    面临的密钥穷举空间为 2^128 (约 3.4 x 10^38 种组合)。")
        print("    以全球现有最强超算算力每秒穷举 100 亿次计算，需要 10^21 年，密码库固若金汤！")
        
    # 5. 真实客户端正常恢复
    print("\n[Step 5] 正式客户端凭完整凭据本地恢复：")
    legit_client = ZeroKnowledgeClient(
        email=email,
        master_password=user_password,
        secret_key=client.secret_key
    )
    recovered_vault = legit_client.decrypt_vault(leaked_dump["vaults_table"][email], salt)
    print("  - 客户端解密成功，核心资产完整还原：")
    print(f"  - 生产数据库密码: {recovered_vault['production_db']['password']}")
    print(f"  - Stripe 核心密钥: {recovered_vault['stripe_api_key'][:15]}...")
    print("\n" + "=" * 70)
    print("   验证结论：零知识双密钥架构成功在服务端彻底失陷时捍卫了核心数据安全！")
    print("=" * 70)

if __name__ == "__main__":
    run_simulation()
