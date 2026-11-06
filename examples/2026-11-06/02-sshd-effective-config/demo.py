#!/usr/bin/env python3
"""用临时配置检查sshd的Match覆盖；不监听端口、不修改系统配置。"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    sshd = shutil.which('sshd') or '/usr/sbin/sshd'
    keygen = shutil.which('ssh-keygen') or '/usr/bin/ssh-keygen'
    if not Path(sshd).is_file():
        raise SystemExit('需要本机已有OpenSSH服务端程序sshd；示例不会安装或启动服务。')
    rows = []
    with tempfile.TemporaryDirectory(prefix='sshd-config-demo-') as tmp:
        folder = Path(tmp)
        # 仅为-T密钥健全性检查生成一次性主机密钥，退出时自动清除。
        subprocess.run([keygen, '-q', '-t', 'ed25519', '-N', '', '-f', str(folder / 'host_key')], check=True, capture_output=True)
        for phase, exception in [('before', 'yes'), ('after', 'no')]:
            config = folder / 'demo.conf'
            config.write_text('HostKey ' + str(folder / 'host_key') + '\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPubkeyAuthentication yes\nMatch User legacy-demo\n    PasswordAuthentication ' + exception + '\n')
            for user in ['developer-demo', 'legacy-demo']:
                result = subprocess.run([sshd, '-T', '-f', str(config), '-C', 'user=' + user + ',host=demo.example,addr=192.0.2.10'], check=True, capture_output=True, text=True)
                effective = dict(line.split(None, 1) for line in result.stdout.splitlines() if line and ' ' in line)
                expected = 'yes' if phase == 'before' and user == 'legacy-demo' else 'no'
                assert effective['passwordauthentication'] == expected
                assert effective['pubkeyauthentication'] == 'yes'
                assert effective['kbdinteractiveauthentication'] == 'no'
                rows.append({'phase': phase, 'user': user, 'passwordauthentication': effective['passwordauthentication'], 'pubkeyauthentication': effective['pubkeyauthentication'], 'kbdinteractiveauthentication': effective['kbdinteractiveauthentication']})
                print(phase + ' ' + user + ' passwordauthentication=' + effective['passwordauthentication'])
    print('only_synthetic_files=true')
    print('server_started=false')
    if args.output:
        with args.output.open('x') as out:
            json.dump({'scope': '配置解析演示；不是漏洞复现、登录测试或生产审计', 'rows': rows, 'server_started': False}, out, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
