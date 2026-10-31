# OCR后的表格结构，怎么变成HTML

本例的输入`input.otsl`是**人工手写的三行样本，不是模型输出**。用Xiaomi-OCR-0官方纯后处理函数转换为HTML，观察合并表头如何变成`colspan="2"`。不识别图片、不运行OCR模型、不下载模型权重，不以本结果评估模型准确率。

环境：Python 3.12.3标准库。依赖一个已完整阅读的官方Python模块，固定commit为`b1a9bb4c07060c453785e9151715ccda6b96f0b1`，许可证见[上游Apache-2.0](https://github.com/xiaomi-research/Xiaomi-OCR-0/blob/b1a9bb4c07060c453785e9151715ccda6b96f0b1/LICENSE)。不安装全局依赖、不需要登录或付费服务。

```bash
python3 table_demo.py
```

命令从固定官方地址读取约8KB模块，核对SHA-256后在临时目录加载，只执行纯表格转换函数，当前目录生成`table.html`。实际输出见`expected.txt`。

已单独下载同一官方模块时，可以离线运行，摘要仍须一致：

```bash
python3 table_demo.py --source /path/to/otsl.py
```

本次联网与离线模式均在临时目录实际运行，输出一致。这个小样本只验证横向合并单元格及三行内容，没有复现OCR基准或整套文档流程。生成的HTML用于本例可信自造输入；将任意文档内容展示到网页前，需按应用自身规则处理HTML，不能把本例当通用清洗器。

来源：[官方后处理代码](https://github.com/xiaomi-research/Xiaomi-OCR-0/blob/b1a9bb4c07060c453785e9151715ccda6b96f0b1/postprocess/otsl.py)、[官方项目说明](https://github.com/xiaomi-research/Xiaomi-OCR-0)。本仓库仅保存独立调用示例，不打包或修改上游模块。
