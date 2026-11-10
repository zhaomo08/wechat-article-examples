"""自造帧时间教学数据，不是任何游戏或Steam样本。"""
from fractions import Fraction
import json,math,platform,tempfile
from pathlib import Path

def summarize(values):
 total=sum(values);sorted_values=sorted(values)
 return {'frames':len(values),'total_ms':round(float(total),2),'fps':round(float(1000*len(values)/total),2),'p95_ms':round(float(sorted_values[math.ceil(len(values)*.95)-1]),2),'over_25ms_pct':round(100*sum(v>25 for v in values)/len(values),2)}

a=[Fraction(50,3)]*600
# 每十帧中8帧12.5毫秒，2帧33.333…毫秒；总时长与A完全相同。
b=[v for _ in range(60) for v in [Fraction(25,2)]*8+[Fraction(100,3)]*2]
result={name:summarize(values) for name,values in [('A 均匀',a),('B 波动',b)]}
assert result['A 均匀']['fps']==result['B 波动']['fps']==60
assert result['B 波动']['over_25ms_pct']==20
assert summarize(list(reversed(b))) == result['B 波动']
with tempfile.TemporaryDirectory(prefix='wechat-frames-') as td:
 p=Path(td)/'result.json';p.write_text(json.dumps(result,ensure_ascii=False));assert json.loads(p.read_text())==result
for label,r in result.items():
 print(f"{label}：{r['frames']}帧 / {r['total_ms']:.2f}ms = {r['fps']:.2f} FPS；P95 {r['p95_ms']:.2f}ms；超过25ms {r['over_25ms_pct']:.0f}%")
print('将B整段倒序：上述汇总指标均不变；时间顺序未保留在这些汇总量里。')
print('P95口径：帧耗时从小到大排序，取ceil(N×0.95)位置；总FPS=总帧数÷总秒数。')
print('环境：Python '+platform.python_version()+'；'+platform.system())
print('范围：人为构造、标准库精确分数计算；不是Steam采样实现或真实游戏测试，不输出视觉流畅度评分。')
if __name__=='__main__':
 Path(__import__('sys').argv[1]).write_text(json.dumps(result,ensure_ascii=False,indent=2)) if len(__import__('sys').argv)>1 else None
