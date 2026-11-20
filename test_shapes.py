# -*- coding: utf-8 -*-
"""
形状自适应测试：
在白纸上放圆���、三角形、五边形、撕开的锯齿形、不规则团块等「非矩形」滤纸片，
验证程序能否找到它们，并且测出的 RGB 不被背景污染。
"""
import os, sys, shutil, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

from detector import DetectConfig, detect_image

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shape_test")

# (名称, 相对原图的比例, 颜色RGB)
SHAPES = [
    ("圆形", "ellipse", (216, 196, 96)),
    ("三角形", "polygon", (200, 176, 110)),
    ("五边形", "pentagon", (176, 160, 130)),
    ("梯形", "trapezoid", (228, 205, 120)),
    ("锯齿撕边", "torn", (186, 170, 112)),
]


def make_shape(kind, cx, cy, r, color):
    """返回一张 RGBA 图，中心在 (cx,cy)，半径 r 的形状"""
    size = r * 2 + 20
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (cx, cy)
    if kind == "ellipse":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,))
    elif kind == "polygon":
        d.polygon([(cx, cy - r), (cx + r, cy + r * 0.8), (cx - r, cy + r * 0.8)],
                  fill=color + (255,))
    elif kind == "pentagon":
        pts = [(cx + r * math.cos(math.pi / 2 + i * 2 * math.pi / 5),
                cy - r * math.sin(math.pi / 2 + i * 2 * math.pi / 5)) for i in range(5)]
        d.polygon(pts, fill=color + (255,))
    elif kind == "trapezoid":
        d.polygon([(cx - r * 0.45, cy - r), (cx + r * 0.45, cy - r),
                   (cx + r, cy + r), (cx - r, cy + r)], fill=color + (255,))
    elif kind == "torn":
        pts = []
        n = 22
        rng = np.random.RandomState(7)
        for i in range(n):
            ang = 2 * math.pi * i / n
            rr = r * (0.72 + 0.28 * rng.rand())
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon(pts, fill=color + (255,))
    return im


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)

    # 造一张「白纸 + 各种形状滤纸片」的照片
    W, H = 3000, 2000
    canvas = Image.new("RGB", (W, H), (238, 237, 235))
    d = ImageDraw.Draw(canvas)
    # 一些干扰：淡淡的桌面纹理、手写字
    for i in range(0, W, 40):
        d.line([(i, 0), (i, H)], fill=(236, 235, 233), width=2)
    d.text((120, 120), "0.001   0.002   0.003   0.004", fill=(40, 40, 40))

    specs = []
    for i, (name, kind, color) in enumerate(SHAPES):
        cx = 300 + i * 560
        cy = 1000
        r = 190
        shp = make_shape(kind, r + 10, r + 10, r, color)
        # 旋转一下，测「任意角度」
        shp = shp.rotate(i * 23, resample=Image.BICUBIC)
        canvas.paste(shp, (cx - r - 10, cy - r - 10), shp)
        specs.append((name, color, (cx - r, cy - r, cx + r, cy + r)))

    path = os.path.join(TMP, "各种形状.jpg")
    canvas.save(path, quality=94)

    cfg = DetectConfig()
    res = detect_image(path, cfg)
    print(f"识别到 {res.n} 片（照片里放了 {len(SHAPES)} 片）")
    print(f"{'形状':<10}{'位置':<26}{'R':>7}{'G':>7}{'B':>7}{'设定值':>18}{'偏差':>8}{'占框%':>7}")
    ok = True
    for d_ in res.detections:
        cx = (d_.bbox[0] + d_.bbox[2]) / 2
        cy = (d_.bbox[1] + d_.bbox[3]) / 2
        best = min(specs, key=lambda s: abs((s[2][0] + s[2][2]) / 2 - cx)
                   + abs((s[2][1] + s[2][3]) / 2 - cy))
        want = best[1]
        got = (d_.rgb_mean[0], d_.rgb_mean[1], d_.rgb_mean[2])
        dev = max(abs(got[i] - want[i]) for i in range(3))
        name = best[0]
        hit = "✓" if dev < 12 else "✗ 偏差大"
        if dev >= 12:
            ok = False
        print(f"{name:<10}{str(d_.bbox):<26}{got[0]:>7.1f}{got[1]:>7.1f}{got[2]:>7.1f}"
              f"{str(want):>18}{dev:>8.1f}{d_.paper_ratio*100:>6.0f}%  {hit}")

    print()
    print("结论：", "各种形状都能识别，且颜色未被背景污染 ✓" if ok and res.n == len(SHAPES)
          else f"存在问题 ✗ (检出 {res.n}/{len(SHAPES)})")
    print("图已保存:", path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
