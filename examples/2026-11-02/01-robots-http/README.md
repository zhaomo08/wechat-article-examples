# robots.txt 与 HTTP 访问是两层事

独立自造例子，只用 Python 3.10+ 标准库。本次在 macOS / Python 3.12.3 运行。

```bash
DEMO_DIR="$(mktemp -d)"
cd "$DEMO_DIR"
python3 /你的路径/wechat-article-examples/examples/2026-11-02/01-robots-http/demo.py
```

脚本在 `127.0.0.1` 随机空闲端口启动临时 HTTP 服务，再访问自己的 robots.txt、公开文章、固定返回401的路径和不存在路径。结束即关闭服务，无公网请求、无文件写入、无真实内容、账号或凭据。真实输出见expected.txt。

客户端没有实现 robots 解析/遵守逻辑；示例因此只能说明：文本中声明用途偏好，不会自动让本机公开文章变成403。它不是厂商爬虫测试、抓取防护、标准符合性测试或可用的身份认证实现。`/private` 总是返回401，没有处理登录或校验密码。

`__usage_ai-training` 来自2026-10-30的 [IETF Internet-Draft](https://www.ietf.org/archive/id/draft-kelley-aipref-training-preference-signal-00.html)，仍是草案。训练用途信号、爬取规则、服务器鉴权要分别看。本例不测试厂商部署日期或实际处理情况。
