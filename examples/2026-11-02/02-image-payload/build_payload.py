"""离线构造两种图片请求格式，不连接模型，不读取真实图片或密钥。"""
import base64
import json
import struct
import zlib
from pathlib import Path


def chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def png_sample():
    width, height = 64, 32
    rows = (b"\0" + bytes((202, 79, 62)) * width) * height
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def main():
    names = ["sample.png", "request-openai.json", "request-anthropic.json"]
    if any(Path(name).exists() for name in names):
        raise SystemExit("目标文件已存在，请换一个临时目录；不覆盖文件。")
    png = png_sample()
    encoded = base64.b64encode(png).decode("ascii")
    data_url = "data:image/png;base64," + encoded
    text = {"type": "text", "text": "请描述图片中的颜色。"}
    openai_image = {"type": "image_url", "image_url": {"url": data_url}}
    anthropic_image = {"type": "image", "source": {
        "type": "base64", "media_type": "image/png", "data": encoded,
    }}
    def payload(image):
        return {"model": "LongCat-2.5", "max_tokens": 1024, "messages": [
            {"role": "user", "content": [text, image]},
        ]}
    left, right = payload(openai_image), payload(anthropic_image)
    raw_left = json.dumps(left, ensure_ascii=False).encode("utf-8")
    raw_right = json.dumps(right, ensure_ascii=False).encode("utf-8")
    with Path(names[0]).open("xb") as f:
        f.write(png)
    for name, data in zip(names[1:], [raw_left, raw_right]):
        with Path(name).open("xb") as f:
            f.write(data)
    a = json.loads(raw_left)["messages"][0]["content"][1]["image_url"]["url"]
    b = json.loads(raw_right)["messages"][0]["content"][1]["source"]["data"]
    assert base64.b64decode(a.split(",", 1)[1], validate=True) == png
    assert base64.b64decode(b, validate=True) == png
    print("sample=synthetic_64x32_png")
    print(f"png_bytes={len(png)}")
    print(f"base64_ascii_bytes={len(encoded)}")
    print(f"openai_json_bytes={len(raw_left)}")
    print(f"anthropic_json_bytes={len(raw_right)}")
    print("openai_blocks=text,image_url")
    print("anthropic_blocks=text,image")
    print("decoded_images_equal=true")
    print("remote_requests=0")


if __name__ == "__main__":
    main()
