import subprocess, os

def kill_leftover():
    """杀掉上次残留的 camoufox/firefox 进程，防止 import 卡死"""
    for name in ("camoufox", "firefox"):
        subprocess.run(
            f'taskkill /F /IM {name}.exe',
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True
        )

kill_leftover()
print("正在加载模块...")
from engine import run_task
print("模块加载完成")

try:
    ok, log = run_task("tasks/stripe_checkout.yaml")
    print("\n".join(log))
    print("\n" + ("=" * 40))
    print("Result:", "SUCCESS" if ok else "FAILED")
except Exception as e:
    log = [str(e)]
    print(f"Error: {e}")
finally:
    kill_leftover()

with open("log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log))
    print("Log saved to log.txt")
