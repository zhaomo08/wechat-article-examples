def destination(scores, threshold=0.80):
    label = max(scores, key=scores.get)
    if label == "其他" or scores[label] < threshold:
        return "人工看一眼"
    return label


cases = [
    ("想取消昨天那笔订单", {"售后": 0.94, "物流": 0.04, "其他": 0.02}),
    ("昨天那个一直没动", {"售后": 0.46, "物流": 0.49, "其他": 0.05}),
    ("这个按钮能换颜色吗", {"售后": 0.04, "物流": 0.02, "其他": 0.94}),
]

for message, example_scores in cases:
    print(f"{message} → {destination(example_scores)}")
