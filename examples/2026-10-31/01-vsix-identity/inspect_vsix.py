"""只读取VSIX样式压缩包清单与SHA-256，不安装、解压或执行扩展。"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def inspect(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(131072), b""):
            digest.update(block)
    with ZipFile(path) as archive:
        names = [x for x in archive.infolist() if x.filename == "extension/package.json"]
        if len(names) != 1 or names[0].file_size > 65536:
            raise ValueError("清单缺失、重复或超过64KiB")
        with archive.open(names[0]) as stream:
            data = stream.read(65537)
        if len(data) > 65536:
            raise ValueError("清单过大")
        manifest = json.loads(data)
    identity = f"{manifest['publisher']}.{manifest['name']}@{manifest['version']}"
    return {"identity": identity, "sha256": digest.hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    args = parser.parse_args()
    print(json.dumps(inspect(args.file), ensure_ascii=False, indent=2))
