# 平均FPS与帧时间分布教学样本

整理日期：2026-11-10。依赖Python3标准库，无额外依赖。

```bash
python3 frame_times.py
```

使用Fraction构造两组均为600帧/10秒的样本，计算总FPS、最近秩P95帧耗时、超过25ms帧占比；把B组倒序后验证汇总量不变。使用临时目录读回结果并自动清理。

真实输出见stdout.txt，数值见result.json。可选传一个输出路径：`python3 frame_times.py /tmp/frame-result.json`。

样本是自造的，不读取游戏/Steam数据，不代表显卡或掌机性能，不推断Valve的采样粒度/权重。25ms是教学阈值，不是行业统一体验界线；P95按ceil(N×0.95)最近秩计算。总FPS=总帧数/总秒数，不等于逐帧倒数的简单平均。
