import subprocess

BASE = r'D:\projects\acesi'
PY = r'C:\Users\gabri\AppData\Local\Programs\Python\Python312\python.exe'
out = subprocess.run(['netstat', '-ano'], capture_output=True, text=True).stdout
pids = set()
for line in out.splitlines():
    if '0.0.0.0:8080' in line and 'LISTENING' in line:
        pids.add(line.split()[-1])
for pid in pids:
    print('killing', pid)
    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
subprocess.Popen(
    [PY, BASE + r'\tools\serve_web.py'],
    cwd=BASE, shell=False, creationflags=0x00000008,
    stdout=open(BASE + r'\tools\web_server.log', 'a', encoding='utf-8'),
    stderr=subprocess.STDOUT,
)
print('static server restarted')
