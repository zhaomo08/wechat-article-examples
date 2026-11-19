"""
Copyright (C) 2026 saymeevetime.cn

@author Chester
@date 2026-11-19
@description Nginx NGINX2Root (CVE-2026-123007) and container security auditor
"""

import os
import sys
import re
import json

SAMPLE_VULNERABLE_CONF = """
user root;
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile        on;

    server {
        listen       443 ssl http2;
        server_name  api.example.com;

        ssl_certificate      /etc/nginx/certs/server.crt;
        ssl_certificate_key  /etc/nginx/certs/server.key;

        location /api/ {
            proxy_pass http://backend_upstream;
        }
    }

    server {
        listen       80;
        server_name  web.example.com;
        http2 on;

        location / {
            root   /usr/share/nginx/html;
            index  index.html;
        }
    }
}
"""

SAMPLE_SECURE_CONF = """
user nginx nginx;
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    server {
        listen       443 ssl;
        server_name  api.example.com;

        # Mitigated: HTTP/2 disabled until upgrading to 1.30.7/1.31.9
        ssl_certificate      /etc/nginx/certs/server.crt;
        ssl_certificate_key  /etc/nginx/certs/server.key;

        location /api/ {
            proxy_pass http://backend_upstream;
        }
    }
}
"""

def audit_nginx_config(content: str):
    findings = []
    
    # 1. 检查运行属主
    user_match = re.search(r'^\s*user\s+([^;]+);', content, re.MULTILINE)
    if user_match:
        user = user_match.group(1).strip()
        if 'root' in user:
            findings.append({
                "severity": "CRITICAL",
                "item": "Worker Process User",
                "detail": f"Nginx configured to run as '{user}'. If worker is compromised, attacker gets root immediately without kernel exploit.",
                "recommendation": "Change to 'user nginx nginx;' or run in non-root container."
            })
        else:
            findings.append({
                "severity": "PASS",
                "item": "Worker Process User",
                "detail": f"Nginx running as unprivileged user: '{user}'."
            })
    else:
        findings.append({
            "severity": "WARNING",
            "item": "Worker Process User",
            "detail": "No explicit 'user' directive found. Defaults to nobody or compile-time user (often root in unhardened containers).",
            "recommendation": "Explicitly configure 'user nginx nginx;'."
        })

    # 2. 检查 HTTP/2 配置（CVE-2026-123007 触发条件）
    h2_listen = re.findall(r'listen\s+[^;]*\bhttp2\b[^;]*;', content)
    h2_directive = re.findall(r'http2\s+on\s*;', content)
    
    if h2_listen or h2_directive:
        count = len(h2_listen) + len(h2_directive)
        locations = []
        if h2_listen:
            locations.extend([l.strip() for l in h2_listen])
        if h2_directive:
            locations.extend([d.strip() for d in h2_directive])
        findings.append({
            "severity": "CRITICAL",
            "item": "HTTP/2 Flow Control Vulnerability (CVE-2026-123007)",
            "detail": f"Detected {count} instances of HTTP/2 enabled: {locations}. Vulnerable to unauthenticated heap overflow RCE.",
            "recommendation": "Emergency mitigation: remove 'http2' parameter from listen directives and remove 'http2 on;'. Upgrade to Nginx >= 1.30.7 or 1.31.9."
        })
    else:
        findings.append({
            "severity": "PASS",
            "item": "HTTP/2 Flow Control Vulnerability",
            "detail": "HTTP/2 is not explicitly enabled. CVE-2026-123007 cannot be triggered over HTTP/1.1."
        })

    return findings

def audit_host_sctp():
    # 检查 Linux SCTP 模块（提权逃逸链关键环节）
    sctp_loaded = False
    if os.path.exists('/sys/module/sctp'):
        sctp_loaded = True
    
    return {
        "item": "Linux Kernel SCTP Module (Privilege Escalation Vector)",
        "sctp_loaded": sctp_loaded,
        "detail": "Kernel SCTP subsystem loaded in memory" if sctp_loaded else "SCTP module is not loaded on this host/container.",
        "risk": "HIGH" if sctp_loaded else "LOW",
        "mitigation": "Add 'blacklist sctp' in /etc/modprobe.d/ or drop CAP_NET_ADMIN in container."
    }

def main():
    print("=" * 70)
    print("  NGINX2Root (CVE-2026-123007) Cluster Security Auditor")
    print("=" * 70)

    print("\n[Stage 1] Scanning Simulated Production Cluster Config (nginx-prod-vuln.conf):")
    findings_vuln = audit_nginx_config(SAMPLE_VULNERABLE_CONF)
    for f in findings_vuln:
        icon = "[FAIL]" if f["severity"] == "CRITICAL" else ("[WARN]" if f["severity"] == "WARNING" else "[OK]")
        print(f"  {icon:<7} {f['item']}")
        print(f"          Detail: {f['detail']}")
        if "recommendation" in f:
            print(f"          Action: {f['recommendation']}")

    print("\n[Stage 2] Scanning Hardened Candidate Config (nginx-prod-patched.conf):")
    findings_sec = audit_nginx_config(SAMPLE_SECURE_CONF)
    for f in findings_sec:
        icon = "[PASS]" if f["severity"] == "PASS" else "[INFO]"
        print(f"  {icon:<7} {f['item']}")
        print(f"          Detail: {f['detail']}")

    print("\n[Stage 3] Checking Linux Host Kernel Defense Boundary (SCTP & Container):")
    sctp_res = audit_host_sctp()
    print(f"  [CHECK] {sctp_res['item']}: {sctp_res['detail']}")
    print(f"          Risk Assessment: {sctp_res['risk']}")
    print(f"          Mitigation: {sctp_res['mitigation']}")

    print("\n[Summary] Emergency Mitigation Quick Reference:")
    print("  1. Sed to disable HTTP/2 instantly without breaking HTTP/1.1 traffic:")
    print("     sed -i -E 's/listen ([0-9]+) ssl http2;/listen \\1 ssl;/g' /etc/nginx/conf.d/*.conf")
    print("     sed -i 's/http2 on;/http2 off;/g' /etc/nginx/nginx.conf")
    print("     nginx -t && nginx -s reload")
    print("  2. K8s Pod Security Context (Block Root & SCTP Escape):")
    print("     securityContext:")
    print("       runAsNonRoot: true")
    print("       allowPrivilegeEscalation: false")
    print("       capabilities:")
    print("         drop: ['ALL']")
    print("=" * 70)

if __name__ == "__main__":
    main()
