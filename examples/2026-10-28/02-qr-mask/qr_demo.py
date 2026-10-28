import cv2
import numpy as np
import qrcode
from qrcode import constants as C

payload = "https://example.com/demo"
qr = qrcode.QRCode(
    version=3, border=4,
    error_correction=C.ERROR_CORRECT_H,
)
qr.add_data(payload)
qr.make(fit=False)
cells = np.array(qr.get_matrix())
original = np.where(cells, 0, 255)
original = original.astype("uint8")
center = len(original) // 2
cases = [
    ("original", 0),
    ("center_7x7", 7),
    ("fully_removed", len(original)),
]
for name, size in cases:
    image = original.copy()
    if size:
        start = center - size // 2
        end = start + size
        image[start:end, start:end] = 255
    image = cv2.resize(
        image, None, fx=12, fy=12,
        interpolation=cv2.INTER_NEAREST,
    )
    cv2.imwrite(name + ".png", image)
    reader = cv2.QRCodeDetector()
    text, _, _ = reader.detectAndDecode(
        image,
    )
    ok = text == payload
    print(name + ":",
          f"matches_original={ok}")
    print(f"  decoded={text!r}")
