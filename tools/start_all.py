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
PORT = os.environ.get('APP_PORT', '8080')
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

if not listening(int(PORT)):
    detach([PY, os.path.join(BASE, 'tools', 'serve_web.py')])
    print('started app on ' + PORT)
else:
    print('app already running')

if not cloudflared_running():
    stamp = time.strftime('%Y%m%d-%H%M%S')
    out_log = os.path.join(LOG_DIR, 'cloudflared_%s.log' % stamp)
    err_log = os.path.join(LOG_DIR, 'cloudflared_%s.err' % stamp)
    detach(
        [CLOUDFLARED, 'tunnel', '--url', 'http://127.0.0.1:' + PORT],
        stdout=out_log, stderr=err_log,
    )
    print('started HTTPS tunnel')
    time.sleep(8)

# Only report the newest tunnel URL. Old quick-tunnel URLs stop working when
# cloudflared restarts, and printing them all is misleading.
url = None
files = [n for n in os.listdir(LOG_DIR)
         if n.startswith('cloudflared_') and n.endswith(('.log', '.err'))]
for name in sorted(files,
                   key=lambda n: os.path.getmtime(os.path.join(LOG_DIR, n)),
                   reverse=True):
    try:
        text = open(os.path.join(LOG_DIR, name), 'r',
                    encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    found = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', text)
    if found:
        url = found[-1]
        break

print()
print('PC app:    http://127.0.0.1:' + PORT)
print('Phone LAN: http://192.168.0.117:' + PORT)
print('HTTPS (current quick tunnel, changes on restart):')
print('  ' + (url or 'not available yet'))
