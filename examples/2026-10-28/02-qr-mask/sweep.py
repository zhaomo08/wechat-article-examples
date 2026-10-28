"""只对自己生成的二维码做中心方块遮挡；不访问网址、不使用AI。"""
import json
from pathlib import Path

import cv2
import numpy as np
import qrcode
from qrcode import constants as C


def main():
    out = Path("outputs")
    out.mkdir(exist_ok=True)
    payload = "https://example.com/demo"
    rows = []
    for level in ("L", "M", "Q", "H"):
        qr = qrcode.QRCode(
            version=3, border=4,
            error_correction=getattr(C, "ERROR_CORRECT_" + level),
        )
        qr.add_data(payload)
        qr.make(fit=False)
        cells = np.array(qr.get_matrix())
        base = np.where(cells, 0, 255).astype("uint8")
        center = len(base) // 2
        flags = []
        for size in (0, 3, 7, 11, 15):
            image = base.copy()
            if size:
                start = center - size // 2
                image[start:start + size, start:start + size] = 255
            image = cv2.resize(image, None, fx=12, fy=12,
                               interpolation=cv2.INTER_NEAREST)
            filename = f"{level}-center-{size}.png"
            cv2.imwrite(str(out / filename), image)
            value, _, _ = cv2.QRCodeDetector().detectAndDecode(image)
            ok = value == payload
            rows.append({"level": level, "covered_modules": size,
                         "matches_original": ok, "decoded": value,
                         "file": filename})
            flags.append(f"{size}:{'OK' if ok else 'FAIL'}")
        print(level + "  " + "  ".join(flags))
    (out / "results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8",
    )


if __name__ == "__main__":
    main()
