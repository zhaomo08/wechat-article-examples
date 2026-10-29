"""自造请求的新旧实现对比；不是Rust性能测试，也不接真实流量。"""
import json


def legacy(request):
    return {"limit": request.get("limit", 20)}


def candidate(request):
    return {"limit": request.get("limit") or 20}


def fixed(request):
    return {"limit": request.get("limit", 20)}


def replay(implementation):
    cases = [("missing", {}), ("positive", {"limit": 10}), ("zero", {"limit": 0})]
    differences = 0
    for name, request in cases:
        old, new = legacy(request), implementation(request)
        same = old == new
        differences += not same
        print(f"{name}: {'SAME' if same else 'DIFF'} old={old['limit']} new={new['limit']}")
    return differences


if __name__ == "__main__":
    print("candidate:")
    assert replay(candidate) == 1
    print("fixed:")
    assert replay(fixed) == 0
