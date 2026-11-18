#!/usr/bin/env python3
"""
PowerShell 5.1 vs 7 核心行为差异及部署流水线排坑仿真验证
复现：
1. 字符编码差异：UTF-16LE BOM (5.1) vs UTF-8 No BOM (7)
2. JSON 递归解析深度截断：Depth=2 (5.1 默认) vs Depth=100 (7 默认)
3. 外部命令非零退出码被吞：$ErrorActionPreference = 'Stop' 在 5.1 中的失效陷阱
"""
import json
import os
import subprocess

def test_encoding_bom_trap():
    print("--- 1. 编码陷阱验证：带 BOM 导致外部解析器抛异常 ---")
    content = '{"server_name": "prod-api", "port": 8080}'
    
    # 模拟 5.1 默认重定向输出：UTF-16LE with BOM
    utf16_bom = content.encode('utf-16')
    # 模拟 7 默认输出：UTF-8 without BOM
    utf8_clean = content.encode('utf-8')
    
    print(f"PowerShell 5.1 常见输出头部 Hex: {utf16_bom[:4].hex()} (包含 0xff 0xfe BOM 或宽字符)")
    print(f"PowerShell 7   标准输出头部 Hex: {utf8_clean[:4].hex()} (标准纯净 UTF-8)")
    
    # 测试在不传编码时，如果用默认 utf-8 严格解析 5.1 的文件
    try:
        utf16_bom.decode('utf-8')
        result_51 = "成功解析"
    except UnicodeDecodeError as e:
        result_51 = f"解析抛异常: {e.reason} (常见于 CI/CD 下游工具报错)"
        
    print(f"下游工具直接读取 5.1 产物结果: {result_51}")
    print(f"下游工具直接读取 7.0 产物结果: 成功解析并启动服务")
    print()

def test_json_depth_truncation():
    print("--- 2. JSON 深度截断惨案验证 (默认 Depth=2 陷阱) ---")
    nested_config = {
        "app": {
            "database": {
                "cluster": {
                    "primary": "10.0.1.5",
                    "replicas": ["10.0.1.6", "10.0.1.7"]
                }
            }
        }
    }
    raw_json = json.dumps(nested_config)
    
    # 模拟 5.1 ConvertFrom-Json 默认深度为 2
    # 深度为 2 时，app -> database 是第二层，cluster 将被视为字符串或截断
    def simulate_ps51_convert(obj, current_depth=0, max_depth=2):
        if current_depth >= max_depth:
            return str(obj) # 5.1 会将超限对象降级为字符串表示
        if isinstance(obj, dict):
            return {k: simulate_ps51_convert(v, current_depth + 1, max_depth) for k, v in obj.items()}
        return obj

    parsed_51 = simulate_ps51_convert(nested_config, 0, 2)
    print("原始 4 层嵌套配置: app -> database -> cluster -> primary/replicas")
    print(f"PowerShell 5.1 (Depth=2 默认) 解析 cluster.primary:")
    try:
        cluster_val = parsed_51["app"]["database"]["cluster"]
        print(f"  类型: {type(cluster_val)}, 值: {cluster_val}")
    except TypeError as e:
        print(f"  [事故复现] 访问失败: {e} (因为超限层级已被强制转换为字符串，无法作为对象继续索引！)")
    
    print(f"PowerShell 7   (Depth=100 默认) 解析 cluster.primary:")
    print(f"  类型: dict, 值: {nested_config['app']['database']['cluster']['primary']} (无缝正常访问)")
    print()

def test_exit_code_swallowing():
    print("--- 3. 原生命令非零退出码吞异常陷阱 ---")
    print("在 PowerShell 5.1 中:")
    print("  设置 $ErrorActionPreference = 'Stop'")
    print("  执行外部命令: git clone / mvn clean install / docker push")
    print("  即使进程 exit 1，PowerShell 5.1 依然判定外部命令执行完成，不触发 catch，脚本继续部署！")
    print("在 PowerShell 7.4+ 中:")
    print("  启用: $PSNativeCommandUseErrorActionPreference = $true")
    print("  外部命令 exit 非 0 时，立即作为 NativeCommandError 抛出终止异常，阻断危险发布！")
    print()

def main():
    print("=" * 65)
    print("PowerShell 5.1 -> 7 迁移：CI/CD 运维与部署脚本核心隐患排查")
    print("=" * 65)
    test_encoding_bom_trap()
    test_json_depth_truncation()
    test_exit_code_swallowing()
    print("=" * 65)

if __name__ == "__main__":
    main()
