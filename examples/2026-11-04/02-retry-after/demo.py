"""本机GET重试教学：不连接DeepSeek、不调用模型、无全局依赖。"""
import argparse
import json
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener


def retry_delay(value):
    if value is None:
        return None
    value = value.strip()
    if value.isascii() and value.isdecimal():
        return float(int(value))
    try:
        at = parsedate_to_datetime(value)
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        return max(0.0, (at - datetime.now(timezone.utc)).total_seconds())
    except (ValueError, TypeError, OverflowError):
        return None


def fetch(url, max_attempts=3, budget=4.0):
    """只用于本机GET。预算在尝试前和等待前检查，不是硬实时期限。"""
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + budget
    waits = []
    for attempt in range(1, max_attempts + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {"status": "budget_exhausted", "attempts": attempt - 1, "waits": waits}
        try:
            with opener.open(url, timeout=min(0.5, remaining)) as response:
                response.read()
                return {"status": response.status, "attempts": attempt, "waits": waits}
        except HTTPError as error:
            status = error.code
            delay = retry_delay(error.headers.get("Retry-After"))
            error.close()
            if status not in (429, 503):
                return {"status": status, "attempts": attempt, "waits": waits}
            if attempt == max_attempts:
                return {"status": "attempts_exhausted", "attempts": attempt, "waits": waits}
            if delay is None:
                delay = min(0.1 * (2 ** (attempt - 1)), 1.0)
            if delay >= deadline - time.monotonic():
                return {"status": "stopped_before_wait", "attempts": attempt, "waits": waits}
            waits.append(delay)
            time.sleep(delay)
        except URLError:
            return {"status": "network_error", "attempts": attempt, "waits": waits}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="可选：另存原始计时JSON，已存在则拒绝覆盖")
    args = parser.parse_args()
    calls = {}
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            with lock:
                samples = calls.setdefault(self.path, [])
                samples.append(time.monotonic())
                count = len(samples)
            if self.path == "/recover":
                status, delay = (503, "1") if count < 3 else (200, None)
            elif self.path == "/budget":
                status, delay = 503, "5"
            else:
                status, delay = 401, None
            body = json.dumps({"ok": status == 200, "local_demo": True}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            if delay is not None:
                self.send_header("Retry-After", delay)
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = "http://127.0.0.1:" + str(server.server_port)
    try:
        recover = fetch(base + "/recover")
        budget = fetch(base + "/budget", budget=0.25)
        unauthorized = fetch(base + "/auth")
        gaps = [b - a for a, b in zip(calls["/recover"], calls["/recover"][1:])]
        assert recover == {"status": 200, "attempts": 3, "waits": [1.0, 1.0]}
        assert min(gaps) >= 0.95
        assert budget == {"status": "stopped_before_wait", "attempts": 1, "waits": []}
        assert unauthorized == {"status": 401, "attempts": 1, "waits": []}
        assert [len(calls[p]) for p in ["/recover", "/budget", "/auth"]] == [3, 1, 1]
        result = {"recover": recover, "recover_observed_gaps_seconds": gaps,
                  "budget": budget, "unauthorized": unauthorized,
                  "network_scope": "127.0.0.1_only", "model_calls": 0}
        if args.output:
            with open(args.output, "x", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                f.write("\n")
        print("recover_status=200")
        print("recover_attempts=3")
        print("recover_retry_wait_seconds=1,1")
        print("recover_min_gap_at_least_0_95s=True")
        print("budget_status=stopped_before_wait")
        print("budget_attempts=1")
        print("unauthorized_status=401")
        print("unauthorized_attempts=1")
        print("network_scope=127.0.0.1_only")
        print("model_calls=0")
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


if __name__ == "__main__":
    main()
