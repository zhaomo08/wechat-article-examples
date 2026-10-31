"""两个无害自造ZIP：清单相同、说明文字不同，不是可安装的真实扩展。"""
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile, ZipInfo
from inspect_vsix import inspect


def make(path, note):
    manifest = {"publisher": "demo", "name": "helper", "version": "1.0.0"}
    with ZipFile(path, "w") as archive:
        for name, content in [
            ("extension/package.json", json.dumps(manifest, sort_keys=True)),
            ("extension/readme.txt", note),
        ]:
            entry = ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            archive.writestr(entry, content)


with tempfile.TemporaryDirectory(prefix="vsix-identity-") as directory:
    a, b = Path(directory) / "a.vsix", Path(directory) / "b.vsix"
    make(a, "A harmless demo.")
    make(b, "Another harmless demo.")
    first, second = inspect(a), inspect(b)
    print("a_identity=" + first["identity"])
    print("b_identity=" + second["identity"])
    print("same_identity=" + str(first["identity"] == second["identity"]).lower())
    print("same_sha256=" + str(first["sha256"] == second["sha256"]).lower())
    print("extension_code_executed=false")
    assert first["identity"] == second["identity"]
    assert first["sha256"] != second["sha256"]
