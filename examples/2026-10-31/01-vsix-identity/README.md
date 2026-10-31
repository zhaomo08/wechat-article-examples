# 同名同版本，不等于同一个文件

本例用Python标准库创建两个无害、不可安装的VSIX样式ZIP：清单里都是`demo.helper@1.0.0`，说明文字不同。只读清单并计算整个文件的SHA-256，没有下载、安装、解压或运行任何真实扩展，也没有访问当前电脑的扩展目录。

```bash
python3 demo.py
```

运行环境：Python 3.12.3、macOS。无第三方依赖、全局修改、账号或网络请求。实际输出见`expected.txt`。

`inspect_vsix.py`也可只读指定小样本清单：

```bash
python3 inspect_vsix.py /path/to/sample.vsix
```

输出不能判定恶意或证明安全。清单自报身份，SHA-256只标识具体字节；真实比对还需要可信渠道、对应平台/版本及可信摘要。模块拒绝缺失/重复/过大的清单，不是完整VSIX验证器、反病毒工具或事件排查工具。

参考：[Cursor官方安全公告](https://cursor.com/blog/claude-code-extension-security-notice)、[Microsoft原始分析](https://www.microsoft.com/en-us/security/blog/2026/10/30/inside-malicious-claude-code-branded-cursor-extension-persistent-ssh-backdoor/)。
