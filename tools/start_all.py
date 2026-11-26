r"""Start ACEsi, the LibSyncStudent web server and the HTTPS tunnel.

Run: python D:\projects\acesi\tools\start_all.py
Safe to run when some or all are already running.
"""
import os
import re
import socket
import subprocess
import time

BASE = r'D:\projects\acesi'
PY = r'C:\Users\gabri\AppData\Local\Programs\Python\Python312\python.exe'
CLOUDFLARED = os.path.join(BASE, 'tools', 'cloudflared.exe')
LOG_DIR = os.path.join(BASE, 'tools')


def listening(port):
    s = socket.socket()
    s.settimeout(0.4)
    ok = s.connect_ex(('127.0.0.1', port)) == 0
    s.close()
    return ok


def cloudflared_running():
    out = subprocess.run(
        ['tasklist', '/FI', 'IMAGENAME eq cloudflared.exe'],
        capture_output=True, text=True, timeout=15,
    ).stdout
    return 'cloudflared.exe' in out


def detach(args, stdout=None, stderr=None):
    kw = dict(cwd=BASE, shell=False, creationflags=0x00000008)
    if stdout:
        kw['stdout'] = open(stdout, 'a', encoding='utf-8')
    if stderr:
        kw['stderr'] = open(stderr, 'a', encoding='utf-8')
    subprocess.Popen(args, **kw)


if not listening(5000):
    detach([PY, 'server.py'])
    print('started ACEsi on 5000')
else:
    print('ACEsi already running')

if not listening(8080):
    detach([PY, os.path.join(BASE, 'tools', 'serve_web.py')])
    print('started app on 8080')
else:
    print('app already running')

if not cloudflared_running():
    stamp = time.strftime('%Y%m%d-%H%M%S')
    out_log = os.path.join(LOG_DIR, 'cloudflared_%s.log' % stamp)
    err_log = os.path.join(LOG_DIR, 'cloudflared_%s.err' % stamp)
    detach(
        [CLOUDFLARED, 'tunnel', '--url', 'http://127.0.0.1:8080'],
        stdout=out_log, stderr=err_log,
    )
    print('started HTTPS tunnel')
    time.sleep(8)

urls = []
for name in os.listdir(LOG_DIR):
    if name.startswith('cloudflared_') and name.endswith('.log'):
        try:
            text = open(os.path.join(LOG_DIR, name), 'r',
                        encoding='utf-8', errors='replace').read()
            urls += re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', text)
        except Exception:
            pass

print()
print('PC app:    http://127.0.0.1:8080')
print('Phone LAN: http://192.168.0.117:8080')
print('HTTPS URLs seen:')
for u in dict.fromkeys(urls):
    print('  ' + u)
