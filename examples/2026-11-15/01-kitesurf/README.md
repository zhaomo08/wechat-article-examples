# 用 Kitesurf 对照 React 页面渲染前后的 HTML

运行环境为 macOS 27.2.1 arm64 和 Node.js 26.8.2。用 Node 自带的 fetch 各发一次 GET，访问 Cloudflare 试玩页列出的同一个 TodoMVC React 示例。

```bash
node compare.mjs
```

脚本断言原始 HTML 中的应用容器为空，渲染后的 HTML 有待办输入框和初始计数。真实运行结果见 [output.txt](output.txt)。

不需 npm 依赖或账号。两个请求都访问公开示例，只读，不提交待办。渲染端为 Cloudflare 提供的公开试玩入口，返回内容或可用性可能随两边的站点更新而变动。实验只核验这个页面上的 DOM，未验证本地构建、成本、性能或其他页面的兼容性。

[试玩入口](https://kitesurf.dev/) · [TodoMVC React 示例](https://todomvc.com/examples/react/dist/index.html) · [Cloudflare 开源公告](https://blog.cloudflare.com/kitesurf-open-source/)
