# 一页 HTML 做确认弹窗

用 Chrome 等现代浏览器直接打开 `index.html`。点击“丢弃草稿”，焦点会落到“取消”。试试点被遮住的“预览清单”按钮，再按 Esc。弹窗关闭后，焦点应回到“丢弃草稿”。数据只在页面内存中变化。

自动验证需要 Node.js、Google Chrome 和项目内 Playwright。把文件复制到临时目录后可以这样跑：

```sh
npm install --no-save playwright
node verify.cjs
```

`output.txt` 是本轮实际 Chrome 验证输出。用 `DIALOG_SCREENSHOT=/tmp/dialog.png node verify.cjs` 可在打开弹窗时抓图。这个样例只核对列出的 Chrome 行为，没有对 Modern Web Guidance 或浏览器矩阵做实测。
