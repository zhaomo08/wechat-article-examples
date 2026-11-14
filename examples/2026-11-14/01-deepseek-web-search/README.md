# DeepSeek 内置网页搜索

用 Python 标准库请求官方 Chat Completions，声明网页搜索工具，输出执行记录和结构化引用。运行需要有余额且有效的 DeepSeek API 密钥。将密钥放在当前环境的 DEEPSEEK_API_KEY 变量中。

```sh
python3 search.py
```

2026-11-14 在 macOS 27.2.1 arm64、Python 3.13.7 运行。实际退出码为 1，官方接口返回 HTTP 401，详见 output.txt。这次没有验证服务端搜索成功。请求体按 [DeepSeek Web Tools 文档](https://api-docs.deepseek.com/guides/web_tools/) 配置。

示例问题有一个可以独立查证的答案。按 [Python 3.14 发布说明](https://docs.python.org/3.14/whatsnew/3.14.html#free-threaded-python-is-officially-supported)，自由线程构建得到正式支持，仍然可选。取得 200 后，可以对照该页面，核对实际搜索是否完成以及回答引用了哪一页。
