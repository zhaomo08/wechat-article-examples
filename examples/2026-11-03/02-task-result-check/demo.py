"""人工清单合并与本地结果检查；不是LifeVal或模型测试。"""
import csv
from pathlib import Path

EXPECTED = {"苹果": 3, "面包": 1}


def write_csv(path, rows):
    with path.open("x", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "quantity"])
        w.writerows(rows)


def check(root, report):
    if report.get("task_id") != "merge-list-01":
        return "FAIL(task_mismatch)"
    if report.get("state") != "completed":
        return "FAIL(not_completed)"
    name = report.get("artifact")
    if not name:
        return "FAIL(missing_file)"
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        return "FAIL(missing_file)"
    try:
        with p.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != ["item", "quantity"]:
                return "FAIL(content_mismatch)"
            rows = list(reader)
        if len(rows) != len(EXPECTED):
            return "FAIL(content_mismatch)"
        actual = {row["item"]: int(row["quantity"]) for row in rows}
    except (ValueError, KeyError, TypeError, OSError):
        return "FAIL(content_mismatch)"
    return "PASS" if actual == EXPECTED else "FAIL(content_mismatch)"


def main():
    root = Path("result-demo")
    root.mkdir()  # 已有同名目录时拒绝覆盖。
    write_csv(root / "input-a.csv", [("苹果", 2), ("面包", 1)])
    write_csv(root / "input-b.csv", [("苹果", 1)])
    merged = {}
    for name in ["input-a.csv", "input-b.csv"]:
        with (root / name).open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                merged[row["item"]] = merged.get(row["item"], 0) + int(row["quantity"])
    write_csv(root / "merged.csv", sorted(merged.items()))
    write_csv(root / "wrong.csv", [("苹果", 2), ("面包", 1)])
    base = {"task_id": "merge-list-01", "state": "completed", "artifact": "merged.csv"}
    cases = {
        "plan_only": {**base, "artifact": None},
        "draft": {**base, "state": "draft"},
        "wrong_quantity": {**base, "artifact": "wrong.csv"},
        "wrong_task": {**base, "task_id": "another-task"},
        "verified": base,
    }
    expected = ["FAIL(missing_file)", "FAIL(not_completed)", "FAIL(content_mismatch)", "FAIL(task_mismatch)", "PASS"]
    results = [check(root, report) for report in cases.values()]
    assert results == expected
    for (name, _), result in zip(cases.items(), results):
        print(f"{name}={result}")
    print("input=handwritten_lists_and_reports")
    print("model_calls=0")
    print("external_actions=0")


if __name__ == "__main__":
    main()
