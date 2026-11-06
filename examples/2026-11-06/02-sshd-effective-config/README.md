# 检查sshd真正生效的认证配置

2026-11-06。Python标准库加本机已有OpenSSH服务端程序`sshd`、`ssh-keygen`；不需要sudo、第三方依赖、网络或账号。不是CVE复现，不启动监听服务。

```bash
python3 demo.py --output result.json
```

脚本在临时目录生成一次性主机密钥和两版虚构配置，分别运行`sshd -T -f <临时配置> -C user=...,host=demo.example,addr=192.0.2.10`。第一版全局关闭密码，但Match为legacy-demo放行；第二版将例外也关闭。实际稳定输出见expected.txt，四个上下文均有断言，JSON另外保存各认证方式。

真实验证环境：macOS 27.0.1 arm64、Python 3.13.7、OpenSSH_10.3p1, LibreSSL 3.3.6；验证了配置解析行为，不能据此判断Alpine漏洞、服务是否重载或是否真正能登录。其他系统缺少sshd或临时测试所需系统条件时会明确失败，不自动安装或修改真实服务。

参考：[sshd -T/-C](https://man.openbsd.org/sshd)、[sshd_config Match](https://man.openbsd.org/sshd_config)、[OpenSSH10.6p2公告](https://www.openssh.org/txt/release-10.6p2)。一次性密钥仅临时生成并销毁，不提交仓库。
