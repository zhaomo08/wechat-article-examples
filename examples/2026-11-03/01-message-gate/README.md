# 跨窗口消息的四个浏览器用例

自造防守示例，不含任何ChatGPT漏洞载荷或复现代码，不连接真实账号、第三方产品或外部服务。三个iframe发出真实浏览器postMessage：合法消息、不同来源、同源但窗口不对、已授权窗口但字段不对。只记录文字，不解释HTML、调用API或执行消息中的代码。

## 运行

需要Node.js、Google Chrome和项目局部安装的Playwright。`verify.cjs`启动两个仅监听127.0.0.1的临时HTTP服务，端口自动分配，测试后关闭。

若没有Playwright，可在临时目录安装，不需要全局安装：

```bash
TEST_DIR="$(mktemp -d)"
npm install --prefix "$TEST_DIR" playwright
NODE_PATH="$TEST_DIR/node_modules" node verify.cjs screenshot.png
```

本次使用本机已有Playwright和Google Chrome，在临时副本中实际测试，没有安装任何依赖。真实输出见expected.txt。截图参数可省略；截图为实际演示页面，不冒充终端或ChatGPT界面。测试没有通过dispatchEvent伪造消息，四个用例都经iframe的postMessage实际发送。

接收端检查origin、source和有限消息格式；发送端使用精确targetOrigin。生产系统仍需结合自己的窗口生命周期、业务授权和限流设计，不能把这个小例子当完整安全方案。

参考：[MDN postMessage](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage)、[WHATWG跨文档消息规范](https://html.spec.whatwg.org/multipage/web-messaging.html#security-postmsg)。
