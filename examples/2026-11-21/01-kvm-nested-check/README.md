# CVE-2026-99312 AMD KVM 嵌套虚拟化穿透漏洞诊断工具

## 背景与原理

CVE-2026-99312 是 Linux 内核 KVM 子系统在 AMD 平台（SVM 嵌套虚拟化）下的高危漏洞。当宿主机开启 `nested=1` 时，KVM 在模拟处理 `INIT` 信号时未能无条件重置 MMU 上下文（stale MMU context），导致嵌套页表（NPT）翻译出现错乱，租户虚拟机可越权直接读取宿主机物理 RAM。

本工具提供针对宿主机及云服务器环境的自动化诊断与加固建议。

## 快速运行

```bash
python3 check_kvm_nested.py
```

## 检测输出示例

```text
======================================================================
CVE-2026-99312 KVM 嵌套虚拟化穿透越界漏洞 - 宿主机安全检测工具
======================================================================

[1] 当前运行节点实际环境检测:
  * CPU 架构/供应商 : Darwin_arm64
  * 内核版本        : 24.3.0
  * 嵌套虚拟化状态  : 未开启/不存在
  * 风险评估        : SAFE (非 AMD 平台或非物理 KVM 宿主，不受 CVE-2026-99312 影响)
  * 防护建议        :
Intel 平台 (VMX) 因硬件级 INIT 无条件拦截机制不受影响；普通虚拟机租户应确认上游云厂商已完成宿主机补丁。

----------------------------------------------------------------------
[2] 模拟受灾云宿主机环境检测 (对比基准):
  * CPU 架构/供应商 : AuthenticAMD (AMD EPYC 9654 96-Core)
  * 内核版本        : 6.12.11-generic (存在 MMU Context Reset 竞态缺陷)
  * 嵌套虚拟化状态  : 开启 (nested=1)
  * 漏洞定性 (CVE)  : CVE-2026-99312 (KVM SVM Stale MMU Context)
  * 风险评估        : CRITICAL (极高危：虚拟机租户可通过 INIT 信号穿透读取宿主物理 RAM)
  * 处置清单        :
1. 紧急升级内核至 7.3.5+ 或安装发行版安全修补包 (Commit: KVM: x86: Unconditionally reset MMU context when emulating INIT)
2. 临时阻断：执行 `sudo modprobe -r kvm_amd && sudo modprobe kvm_amd nested=0`
3. 持久化规避：在 `/etc/modprobe.d/kvm.conf` 写入 `options kvm_amd nested=0`
======================================================================
```
