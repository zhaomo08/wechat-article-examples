"""运行一次 DeepSeek 内置网页搜索，只打印公开答案、引用和用量。"""
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

question = (
    "请实际使用网页搜索。只根据 Python 官方文档回答："
    "Python 3.14 的 free-threaded Python 是否仍是实验特性，"
    "它是否变成默认构建？用两句中文回答，并附官方引用。"
)
payload = {
    "model": "deepseek-flash",
    "thinking": {"type": "disabled"},
    "tools": [{"type": "deepseek_web_search"}],
    "messages": [{"role": "user", "content": question}],
    "max_tokens": 650,
}
request = Request(
    "https://api.deepseek.com/chat/completions",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"],
        "Content-Type": "application/json",
    },
)
try:
    with urlopen(request, timeout=60) as response:
        print(f"HTTP {response.status}")
        result = json.load(response)
except HTTPError as error:
    sys.exit(f"HTTP {error.code}，请检查官方错误码说明和账户状态。")

choice = result["choices"][0]
message = choice["message"]
calls = [call for step in message.get("server_tool_calls", []) for call in step["calls"]]
citations = [
    item["url_citation"]["url"]
    for item in message.get("annotations", [])
    if item["type"] == "url_citation"
]
print(f"model: {result['model']}")
print(f"finish_reason: {choice['finish_reason']}")
for call in calls:
    print(f"{call['kind']}: {call['status']}")
print("answer:", message.get("content"))
for url in dict.fromkeys(citations):
    print("citation:", url)
print("server_tool_use:", json.dumps(result["usage"].get("server_tool_use", {})))
if not citations or not any(call["status"] == "completed" for call in calls):
    sys.exit("没有同时取得已完成的工具调用和结构化引用。")
