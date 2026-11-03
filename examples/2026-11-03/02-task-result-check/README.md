# 任务说明与实际文件分开检查

Python3.10+标准库示例，本次macOS/Python3.13.7验证。输入为两份人工购物清单和人工状态报告；程序真实合并CSV、写出merged.csv，再检查任务ID、完成状态、文件存在和固定内容预期。没有下单、预约或模型调用。

```bash
DEMO_DIR="$(mktemp -d)"
cd "$DEMO_DIR"
python3 /你的路径/wechat-article-examples/examples/2026-11-03/02-task-result-check/demo.py
```

生成当前目录下的result-demo/，已有同名目录则拒绝覆盖。真实输出见expected.txt。正确文件为苹果3、面包1；人工反例包括没有文件、仍为草稿、数量错误和任务身份错误。

这是本地机械要求的教学例子，不是OpenAI LifeVal实现、官方数据、评测结果或模型成功率。固定预期只适用于这个已知人工任务，也不能判断规划好坏、外部服务状态或现实世界是否完成了某个动作。不能把这个PASS当作真实购物/预约成功。
