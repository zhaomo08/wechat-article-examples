# 图片请求的两种格式

按 [LongCat视觉理解文档](https://longcat.chat/platform/docs/image-video-understanding)离线构造OpenAI兼容和Anthropic兼容格式。只用Python3.10+标准库，本次macOS/Python3.12.3验证。模型名LongCat-2.5、max_tokens=1024为文档格式下的样例值；没有调用API确认服务端是否接受。

```bash
DEMO_DIR="$(mktemp -d)"
cd "$DEMO_DIR"
python3 /你的路径/wechat-article-examples/examples/2026-11-02/02-image-payload/build_payload.py
```

生成一张64×32的纯色人工PNG，以及request-openai.json、request-anthropic.json；已有任一同名文件就拒绝覆盖。PNG的Base64编码解码往返和两份JSON可解析性已验证，真实输出在expected.txt。仅在临时目录生成小型产物，不写全局配置、不装依赖、不下载权重或访问网络。

样例JSON不含endpoint、鉴权header、API Key或真实数据。本例只验证本地组包、PNG编码和解码，不代表LongCat推理、视觉质量、服务可用性或厂商兼容性测试。需要实际调用时，应另按当前官方接口选择路径、配置自己的凭据，先确认预算和数据范围；此脚本没有发送功能。

Base64字符数增加是编码体积，不是模型视觉token或账单。不要把请求体字节数当作推理token数。
