# 公开文章链接参数处理

Python标准库即可运行：

```bash
python3 clean_links.py
```

示例只处理`example.com/articles/`下的自造地址，只删除明确配置的utm_source、utm_medium、utm_campaign三个键，保留其他参数、重复键、空值、编码形式与片段。通过保留原始参数片段，避免解码后重新编码改变其他字段。

已知签名/令牌键出现时直接保持原串；其他域名和路径同样不改，不请求网络、不展开短链。`host`参数可以改为自己已确认规则的公开文章站点；不要把下载签名、支付、登录、回调等链接加进处理范围。已知键的保护不可能识别全部站点的私有协议，不能把这个示例称为通用安全清理器。

未知参数a保留。仓库没有证据确认当前X分享链接a参数的含义，脚本也不处理X链接。示例数据不含实际凭据。

来源：[Python URL解析](https://docs.python.org/3.12/library/urllib.parse.html)、[Google Analytics UTM定义](https://support.google.com/analytics/answer/10917952?hl=en)、[RFC3986](https://www.rfc-editor.org/rfc/rfc3986.html)。
