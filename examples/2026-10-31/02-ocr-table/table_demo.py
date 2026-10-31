"""人工OTSL样本经过官方纯后处理函数；不运行OCR模型。"""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
from urllib.request import Request, urlopen

URL = "https://raw.githubusercontent.com/xiaomi-research/Xiaomi-OCR-0/b1a9bb4c07060c453785e9151715ccda6b96f0b1/postprocess/otsl.py"
SHA256 = "db46f5a05d9742a7bcfd3931428bdd9e8de845892b66fa4cf09bd21f83cf2b14"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="离线使用已下载的同一官方模块，仍校验SHA-256")
    args = parser.parse_args()
    if args.source:
        source = Path(args.source).read_bytes()
    else:
        with urlopen(Request(URL, headers={"User-Agent": "ocr-postprocess-demo/1.0"}), timeout=20) as response:
            source = response.read(16385)
    if len(source) > 16384 or hashlib.sha256(source).hexdigest() != SHA256:
        raise ValueError("官方模块大小或摘要不匹配，停止")
    with tempfile.TemporaryDirectory(prefix="ocr-table-") as directory:
        module_path = Path(directory) / "otsl.py"
        module_path.write_bytes(source)
        spec = importlib.util.spec_from_file_location("pinned_otsl", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        sample = Path(__file__).with_name("input.otsl").read_text()
        result = module.convert_otsl_to_html(sample)
        del sys.modules[spec.name]
    assert '<td colspan="2">费用</td>' in result
    assert result.count("<tr>") == 3 and "12.00" in result
    Path("table.html").write_text(result)
    print("input_kind=handwritten_demo_tokens")
    print("model_inference_run=false")
    print("merged_header_colspan_2=true")
    print(result)


if __name__ == "__main__":
    main()
