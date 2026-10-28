# 结构化输出校验

这是接收模型返回值时的一小段应用代码。使用人工构造的六个JSON样本演示结构校验，**没有调用LFM3或其他模型，不是模型准确率评测**。

## 运行

Python3.12.3验证通过，无第三方依赖：

```bash
python3 check_output.py
```

输出见 [expected.txt](expected.txt)。也可校验自己的JSON文件：

```bash
python3 check_output.py --input your-output.json
```

只允许category与summary两个字段；category为bug、feature、question之一；summary须为去除首尾空白后1–80字符的文本。单文件校验失败退出1。

`semantically_wrong`故意把“登录页500错误”标为feature，仍会被接受，说明结构正确无法保证分类含义正确。不要把这个检查当成可执行工具调用的授权，也不能据此声称某个模型分类可靠。
