from flask import Flask, request, jsonify
from engine import run_task
import threading

app = Flask(__name__)

tasks = {}
task_id_counter = 0
lock = threading.Lock()


def run_in_background(tid, task_file, variables):
    with lock:
        tasks[tid]["status"] = "running"
    try:
        ok, log = run_task(task_file, variables)
        with lock:
            tasks[tid]["status"] = "success" if ok else "failed"
            tasks[tid]["log"] = log
    except Exception as e:
        with lock:
            tasks[tid]["status"] = "error"
            tasks[tid]["log"].append(str(e))


@app.route("/run", methods=["POST"])
def run():
    """启动任务 / Start task
    POST /run
    {
        "task": "tasks/stripe_checkout.yaml",
        "vars": {"邮箱": "xxx", "密码": "xxx"}
    }
    """
    global task_id_counter
    data = request.json or {}
    task_file = data.get("task", "tasks/stripe_checkout.yaml")
    variables = data.get("vars", {})

    with lock:
        task_id_counter += 1
        tid = task_id_counter
        tasks[tid] = {"status": "pending", "log": []}

    t = threading.Thread(target=run_in_background, args=(tid, task_file, variables))
    t.start()

    return jsonify({"task_id": tid, "status": "started"})


@app.route("/status/<int:tid>")
def status(tid):
    """查询任务状态 / Get task status"""
    with lock:
        if tid not in tasks:
            return jsonify({"error": "task not found"}), 404
        t = tasks[tid]
        return jsonify({"task_id": tid, "status": t["status"], "log": list(t["log"])})


@app.route("/tasks")
def list_tasks():
    """列出所有任务 / List all tasks"""
    with lock:
        return jsonify({tid: {"status": t["status"]} for tid, t in tasks.items()})


@app.route("/clear", methods=["POST"])
def clear():
    """清理已完成的任务 / Clear finished tasks"""
    with lock:
        finished = [tid for tid, t in tasks.items() if t["status"] in ("success", "failed", "error")]
        for tid in finished:
            del tasks[tid]
        return jsonify({"cleared": len(finished)})


if __name__ == "__main__":
    from waitress import serve
    print("Service running on http://localhost:5000")
    serve(app, host="0.0.0.0", port=5000)
