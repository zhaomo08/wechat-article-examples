"""校验人工构造的JSON输出；不调用模型或外部服务。"""
import argparse
import json
from pathlib import Path


def check_output(raw):
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("输出必须是对象")
    if set(obj) != {"category", "summary"}:
        raise ValueError("字段必须是category和summary")
    category = obj["category"]
    if not isinstance(category, str) or category not in {"bug", "feature", "question"}:
        raise ValueError("category超出约定范围")
    summary = obj["summary"]
    if not isinstance(summary, str) or not 1 <= len(summary.strip()) <= 80:
        raise ValueError("summary必须是1到80字符的文本")
    return {"category": category, "summary": summary.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="校验单个JSON文件，失败时退出1")
    args = parser.parse_args()
    if args.input:
        try:
            obj = check_output(args.input.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            parser.exit(1, f"拒绝：{exc}\n")
        print(json.dumps(obj, ensure_ascii=False))
        return
    samples = Path(__file__).with_name("samples.json")
    for case in json.loads(samples.read_text(encoding="utf-8")):
        try:
            obj = check_output(case["raw"])
            print(f'{case["name"]}: 接受 category={obj["category"]}')
        except ValueError as exc:
            print(f'{case["name"]}: 拒绝 {exc}')


if __name__ == "__main__":
    main()
