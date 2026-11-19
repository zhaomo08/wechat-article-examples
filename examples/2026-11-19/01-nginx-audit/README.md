# Nginx NGINX2Root (CVE-2026-123007) 漏洞排查与配置防御工具

针对 2026 年 11 月 19 日披露的 NGINX2Root 高危漏洞链，提供线上集群配置扫描与安全加固检测脚本。

## 核心排查项目
1. **HTTP/2 开启状态扫描**：检测是否开启易受 CVE-2026-123007 堆溢出攻击的 HTTP/2 模块。
2. **Worker 运行属主检测**：排查 Nginx Worker 是否直接以 `root` 特权运行。
3. **Linux 内核逃逸面核查**：检测宿主机/容器是否加载了 SCTP 内核模块或存在未隔离特权。

## 运行方式
```bash
python3 nginx_vuln_auditor.py
```

## 紧急加固命令速查
若无法立即升级至 Nginx 1.30.7 或 1.31.9，可执行以下命令就地关闭 HTTP/2 缓解：
```bash
# 1. 替换配置文件中的 http2 监听与指令
sed -i -E 's/listen ([0-9]+) ssl http2;/listen \1 ssl;/g' /etc/nginx/conf.d/*.conf
sed -i 's/http2 on;/http2 off;/g' /etc/nginx/nginx.conf

# 2. 语法测试与平滑重载
nginx -t && nginx -s reload
```
