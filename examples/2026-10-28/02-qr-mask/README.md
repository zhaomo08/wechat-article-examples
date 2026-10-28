# 二维码遮挡实验

生成只含`https://example.com/demo`的自造样本，再用OpenCV读取。不访问该网址、不使用AI或付费API，也不处理他人的票券、登录码或凭证。

## 安装与运行

已验证Python3.12.3、macOS27.0.1 arm64：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python qr_demo.py
.venv/bin/python sweep.py
```

`qr_demo.py`保存原图、中心7×7模块涂白、整张清空三张PNG，结果与文章三张图对应。`sweep.py`固定Version3和相同内容，分别测试L/M/Q/H四种纠错级别，以及0、3、7、11、15个模块边长的中心方块。它会在outputs/生成20张PNG和results.json。示例输出见 [expected.txt](expected.txt)。

## 怎么理解结果

OK表示解码文本与原文完全一致，FAIL表示本次OpenCV未读回相同文本。H级约30%指码字纠错口径，不是任意图片面积的遮挡比例。改变版本、内容、遮挡位置、图像缩放或解码器，都可能改变结果。

该实验没有复现新闻中的AI马赛克修复，也不提供“遮住多少就安全”的通用阈值。输出图和结果JSON不上传仓库，运行后自行查看。

来源：[DENSO WAVE纠错说明](https://www.qrcode.com/en/about/error_correction.html)、[版本说明](https://www.qrcode.com/en/about/version.html)、[python-qrcode](https://github.com/lincolnloop/python-qrcode)、[OpenCV](https://docs.opencv.org/4.12.0/d7/d90/classcv_1_1GraphicalCodeDetector.html)。
