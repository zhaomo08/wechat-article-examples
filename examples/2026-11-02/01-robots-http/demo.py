"""本机 HTTP 演示：robots.txt 声明不会自动变成服务器访问控制。"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

ROBOTS = b"User-agent: __usage_ai-training\nDisallow: /\n\nUser-agent: *\nAllow: /\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/robots.txt":
            status, body = 200, ROBOTS
        elif self.path == "/article":
            status, body = 200, b"Public demo article"
        elif self.path == "/private":
            status, body = 401, b"Authentication required"
        else:
            status, body = 404, b"Not found"
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def read(url):
    try:
        with urlopen(url, timeout=3) as response:
            return response.status, response.read()
    except HTTPError as error:
        with error:
            return error.code, error.read()


def main():
    # 只监听回环地址，由操作系统选择空闲端口，不访问公网或真实站点。
    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            rs, policy = read(base + "/robots.txt")
            ps, article = read(base + "/article")
            private, _ = read(base + "/private")
            missing, _ = read(base + "/missing")
            assert (rs, ps, private, missing) == (200, 200, 401, 404)
            assert policy == ROBOTS and article == b"Public demo article"
            print(f"robots_status={rs}")
            print(f"training_policy_declared={'__usage_ai-training' in policy.decode()}")
            print(f"public_article_status={ps}")
            print(f"public_article_body={article.decode()}")
            print(f"private_status_without_auth={private}")
            print(f"missing_path_status={missing}")
            print("external_requests=0")
        finally:
            server.shutdown()
            thread.join(timeout=3)


if __name__ == "__main__":
    main()
