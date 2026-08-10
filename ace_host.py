# ace_host.py — self-hosting watchdog for ACEsi.
# Runs `python -u server.py` as a child, restarts it on crash or when the
# restart flag is set, and health-checks the API. Usage: python ace_host.py
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(HERE, "ace_host.pid")
FLAG_FILE = os.path.join(HERE, "ace_host.flag")
LOG_FILE = os.path.join(HERE, "ace_host.log")
HEALTH_URL = "http://127.0.0.1:5000/opencode/status"
CHILD_RESTART_DELAY = 3  # seconds the old child gets to wind down after a flag restart


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def read_flag():
    try:
        with open(FLAG_FILE) as f:
            return f.read().strip()
    except Exception:
        return ""


def clear_flag():
    try:
        os.remove(FLAG_FILE)
    except OSError:
        pass


def http_ok():
    try:
        import urllib.request
        with urllib.request.urlopen(HEALTH_URL, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def spawn():
    return subprocess.Popen([sys.executable, "-u", "server.py"],
                            cwd=HERE, creationflags=subprocess.DETACHED_PROCESS,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    write_pid()
    log("ace_host watchdog starting")
    child = spawn()
    log("server started (pid %d)" % child.pid)
    dead_checks = 0
    while True:
        time.sleep(2)
        flag = read_flag()
        if flag == "stop":
            clear_flag()
            log("stop flag received — terminating")
            child.terminate()
            return
        if flag == "restart":
            clear_flag()
            log("restart flag received")
            child.terminate()
            try:
                child.wait(timeout=CHILD_RESTART_DELAY)
            except subprocess.TimeoutExpired:
                child.kill()
            child = spawn()
            log("server restarted (pid %d)" % child.pid)
            dead_checks = 0
            continue
        alive = child.poll() is None
        if not alive:
            log("server died (code %s) — restarting" % child.returncode)
            child = spawn()
            log("server restarted (pid %d)" % child.pid)
            dead_checks = 0
            continue
        if http_ok():
            dead_checks = 0
        else:
            dead_checks += 1
            if dead_checks >= 15:  # ~30s without an HTTP response
                log("server unresponsive — restarting")
                child.terminate()
                try:
                    child.wait(timeout=CHILD_RESTART_DELAY)
                except subprocess.TimeoutExpired:
                    child.kill()
                child = spawn()
                log("server restarted (pid %d)" % child.pid)
                dead_checks = 0


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
