# 先发已经准备好的HTML

Node.js内置http模块，无npm依赖、全局安装、账号或外部请求。两条本机路由都人为等待800ms准备明细，最终HTML相同；stream路径先发送已就绪的资料卡，buffered路径等明细齐了才发。

```bash
node demo.mjs --output result.json
```

稳定输出见expected.txt；result.json保存实际首块数据和完整响应耗时，已存在时拒绝覆盖。脚本自动关闭本机服务。这里测HTTP正文数据抵达，不是浏览器首屏、X的重写复刻、吞吐压测或真实慢网效果。

想在浏览器看中间状态：

```bash
node demo.mjs --serve
```

打开终端输出的本机stream或buffered链接，结束时Ctrl+C。仅监听127.0.0.1，随机空闲端口。HTML里的点状注释只是帮助观察浏览器对小响应的缓冲，不是生产优化技巧。本例没有React、hydration、鉴权、压缩或反向代理，也不处理生产中的取消与背压。Node在没有Content-Length且分段写入时使用HTTP/1.1分块传输；HTTP/2的帧机制不同，别照抄Transfer-Encoding头。

依据：[X工程公告](https://blog.x.com/en/engineering/rebuilding-the-global-town-square-from-scratch)、[Node HTTP write](https://nodejs.org/api/http.html#responsewritechunk-encoding-callback)、[React流式SSR](https://react.dev/reference/react-dom/server/renderToPipeableStream)。
