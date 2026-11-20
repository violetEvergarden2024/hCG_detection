# -*- coding: utf-8 -*-
"""生成应用图标 app.ico（一片滤纸 + 显色圆斑）"""
import os
import math
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))


def make(size=256):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 圆角深色底
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22),
                        fill=(24, 28, 38, 255))
    # 一片斜放的方形滤纸
    m = int(S * 0.18)
    d.polygon([(m + int(S * 0.06), m), (S - m, m + int(S * 0.05)),
               (S - m - int(S * 0.05), S - m), (m, S - m - int(S * 0.04))],
              fill=(238, 236, 230, 255))
    # 显色圆斑（黄色渐变感）
    cx, cy, r = int(S * 0.48), int(S * 0.52), int(S * 0.22)
    for i in range(r, 0, -1):
        t = i / float(r)
        col = (int(214 - 40 * (1 - t)), int(190 - 30 * (1 - t)),
               int(96 + 40 * (1 - t)), 255)
        rr = int(r * (i / float(r)))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
    # 白色高光
    d.ellipse([cx - r // 2, cy - r // 2, cx + r // 8, cy + r // 8],
              fill=(255, 255, 255, 90))
    # 小圆片（示意支持任意形状）
    cx2, cy2, r2 = int(S * 0.70), int(S * 0.30), int(S * 0.10)
    d.ellipse([cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2], fill=(120, 190, 250, 255))
    return im.resize((size, size), Image.LANCZOS)


def main():
    base = make(256)
    ico = os.path.join(HERE, "app.ico")
    base.save(ico, format="ICO", sizes=[(256, 256), (128, 128), (64, 64),
                                         (48, 48), (32, 32), (16, 16)])
    print("图标已生成:", ico)
    # 顺便留一张 png 方便预览
    base.save(os.path.join(HERE, "app_icon.png"))


if __name__ == "__main__":
    main()
