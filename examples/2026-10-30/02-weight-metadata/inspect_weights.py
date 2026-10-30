"""只统计文件清单的字节数，不下载权重，不运行模型。"""
import argparse
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

REPOSITORY = "mistralai/Mistral-Large-4-1T-A52B"
REVISION = "f12dabdc0c1e99e7f7924461a6f308859b05af4d"
URL = f"https://huggingface.co/api/models/{REPOSITORY}/tree/{REVISION}?recursive=false&expand=false"


def summarize(files):
    shards = []
    for item in files:
        match = re.fullmatch(r"consolidated-(\d+)-of-(\d+)\.safetensors", item["path"])
        if match:
            if not isinstance(item.get("size"), int) or item["size"] <= 0:
                raise ValueError("无效的分片大小")
            shards.append((int(match[1]), int(match[2]), item["size"]))
    if not shards:
        raise ValueError("清单中没有目标分片")
    expected = shards[0][1]
    if (any(n != expected for _, n, _ in shards)
            or len(shards) != expected
            or {i for i, _, _ in shards} != set(range(1, expected + 1))):
        raise ValueError("清单不完整或含重复分片，不能当成完整大小")
    return len(shards), sum(size for _, _, size in shards)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="联网读取固定revision的JSON清单，最大1MB")
    args = parser.parse_args()
    if args.refresh:
        with urlopen(Request(URL, headers={"User-Agent": "weight-metadata-demo/1.0"}), timeout=30) as response:
            payload = response.read(1_000_001)
        if len(payload) > 1_000_000:
            raise ValueError("元数据超过限制，停止")
        files = json.loads(payload)
    else:
        snapshot = json.loads(Path(__file__).with_name("manifest.json").read_text())
        if snapshot["repository"] != REPOSITORY or snapshot["revision"] != REVISION:
            raise ValueError("快照来源与固定revision不一致")
        files = snapshot["files"]
    count, size = summarize(files)
    print("checkpoint_shards=" + str(count))
    print("checkpoint_bytes=" + str(size))
    print(f"checkpoint_TB_decimal={size / 10**12:.3f}")
    print(f"checkpoint_TiB={size / 2**40:.3f}")
    print("weights_downloaded=false")
    print("model_inference_run=false")


if __name__ == "__main__":
    main()
