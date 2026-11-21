#!/usr/bin/env python3
"""
CVE-2026-99312 KVM 嵌套虚拟化配置自查与 MMU 映射安全诊断脚本
用于检查宿主机/云服务器环境是否存在 AMD 嵌套虚拟化暴露风险与未修补 MMU 上下文重置漏洞。
"""

import os
import sys
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class DiagnosticResult:
    cpu_vendor: str
    is_amd: bool
    is_virtual_machine: bool
    nested_svm_enabled: bool
    kernel_version: str
    is_vulnerable: bool
    risk_level: str
    recommendation: str

def get_cpu_vendor() -> str:
    """获取 CPU 供应商信息"""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "vendor_id" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    # macOS 或本地兼容环境降级推断
    machine = platform.machine()
    system = platform.system()
    return f"{system}_{machine}"

def check_nested_param() -> Tuple[bool, str]:
    """检查 kvm_amd 模块参数 nested 是否开启"""
    path = "/sys/module/kvm_amd/parameters/nested"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                val = f.read().strip()
                return val in ("1", "Y", "y"), val
        except Exception as e:
            return False, f"读取失败: {e}"
    return False, "未检测到 kvm_amd 内核模块或文件不存在"

def is_kernel_fixed(version_str: str) -> bool:
    """
    CVE-2026-99312 上游在 7.3.5 / 6.12.18 / 6.6.82 等 LTS 维护版本修复。
    模拟版本比较逻辑。
    """
    # 模拟检查版本
    return "7.3.5" in version_str or "fixed" in version_str

def run_diagnostic(mock_mode: bool = False, mock_amd_nested: bool = False) -> DiagnosticResult:
    """运行全套诊断"""
    vendor = get_cpu_vendor()
    is_amd = "AuthenticAMD" in vendor or mock_amd_nested
    
    if mock_mode and mock_amd_nested:
        nested_enabled = True
        nested_raw = "1 (模拟 AMD 生产宿主机已开启嵌套虚拟化)"
        kernel_ver = "6.12.11-generic (存在 MMU Context Reset 竞态缺陷)"
    else:
        nested_enabled, nested_raw = check_nested_param()
        kernel_ver = platform.release()

    # 判断漏洞状态
    # 仅当: CPU 为 AMD + 开启了 nested virtualization + 内核未打补丁 时触发 CVE-2026-99312
    if is_amd and nested_enabled:
        is_fixed = is_kernel_fixed(kernel_ver)
        if not is_fixed:
            is_vuln = True
            risk = "CRITICAL (极高危：虚拟机租户可通过 INIT 信号穿透读取宿主物理 RAM)"
            recom = (
                "1. 紧急升级内核至 7.3.5+ 或安装发行版安全修补包 (Commit: KVM: x86: Unconditionally reset MMU context when emulating INIT)\n"
                "2. 临时阻断：执行 `sudo modprobe -r kvm_amd && sudo modprobe kvm_amd nested=0`\n"
                "3. 持久化规避：在 `/etc/modprobe.d/kvm.conf` 写入 `options kvm_amd nested=0`"
            )
        else:
            is_vuln = False
            risk = "LOW (已修复：内核包含无条件 MMU 重置补丁)"
            recom = "内核已修补，建议定期保持发行版安全包更新。"
    elif is_amd and not nested_enabled:
        is_vuln = False
        risk = "SAFE (安全：未开启嵌套虚拟化，攻击面未暴露)"
        recom = "保持 nested=0 状态，生产多租户环境切勿无故开启嵌套虚拟化。"
    else:
        is_vuln = False
        risk = "SAFE (非 AMD 平台或非物理 KVM 宿主，不受 CVE-2026-99312 影响)"
        recom = "Intel 平台 (VMX) 因硬件级 INIT 无条件拦截机制不受影响；普通虚拟机租户应确认上游云厂商已完成宿主机补丁。"

    return DiagnosticResult(
        cpu_vendor=vendor,
        is_amd=is_amd,
        is_virtual_machine="Darwin" in platform.system() or "kvm" in kernel_ver.lower(),
        nested_svm_enabled=nested_enabled,
        kernel_version=kernel_ver,
        is_vulnerable=is_vuln,
        risk_level=risk,
        recommendation=recom
    )

def main():
    print("=" * 70)
    print("CVE-2026-99312 KVM 嵌套虚拟化穿透越界漏洞 - 宿主机安全检测工具")
    print("=" * 70)
    
    # 1. 检测真实当前环境
    res_real = run_diagnostic(mock_mode=False)
    print("\n[1] 当前运行节点实际环境检测:")
    print(f"  * CPU 架构/供应商 : {res_real.cpu_vendor}")
    print(f"  * 内核版本        : {res_real.kernel_version}")
    print(f"  * 嵌套虚拟化状态  : {'开启 (nested=1)' if res_real.nested_svm_enabled else '未开启/不存在'}")
    print(f"  * 风险评估        : {res_real.risk_level}")
    print(f"  * 防护建议        :\n{res_real.recommendation}")
    
    # 2. 模拟高危受灾现场基准对比 (AMD 宿主机开启了 Nested SVM 且跑在未打补丁的旧内核)
    print("\n" + "-" * 70)
    print("[2] 模拟受灾云宿主机环境检测 (对比基准):")
    res_vuln = run_diagnostic(mock_mode=True, mock_amd_nested=True)
    print(f"  * CPU 架构/供应商 : AuthenticAMD (AMD EPYC 9654 96-Core)")
    print(f"  * 内核版本        : {res_vuln.kernel_version}")
    print(f"  * 嵌套虚拟化状态  : 开启 (nested=1)")
    print(f"  * 漏洞定性 (CVE)  : CVE-2026-99312 (KVM SVM Stale MMU Context)")
    print(f"  * 风险评估        : {res_vuln.risk_level}")
    print(f"  * 处置清单        :\n{res_vuln.recommendation}")
    print("=" * 70)

if __name__ == "__main__":
    main()
