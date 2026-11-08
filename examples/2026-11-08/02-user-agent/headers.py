import threading,json,urllib.request,platform
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
seen=[]
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  seen.append({'path':self.path,'user_agent':self.headers.get('User-Agent')});self.send_response(200);self.end_headers();self.wfile.write(b'ok')
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
try:
 for ua in ['ArticleDemo/1.0 (contact: demo@example.invalid)','ArticleDemo/1.0']:
  req=urllib.request.Request(f'http://127.0.0.1:{server.server_port}/check',headers={'User-Agent':ua})
  with urllib.request.urlopen(req) as r:assert r.status==200
 assert seen[0]['user_agent'].endswith('demo@example.invalid)') and '@' not in seen[1]['user_agent']
 print('请求 A，接收端看到：'+seen[0]['user_agent'])
 print('请求 B，接收端看到：'+seen[1]['user_agent'])
 print('两次路径均为 /check；邮箱位于请求头，未出现在 URL。')
 print('环境：Python '+platform.python_version()+'；'+platform.system())
 print('范围：仅本机 127.0.0.1；邮箱为保留示例域名；未调用 Claude Code，未发送真实个人信息。')
finally:server.shutdown();server.server_close();t.join()
