# -*- coding: utf-8 -*-
"""
圆形滤纸片专项测试
==================
模拟几种真实场景里会出现圆形纸片（圆形滤纸片 / 打孔的圆片）的情况：

  1. 大圆片（带手写浓度标注）
  2. 中等圆片
  3. 小圆片
  4. 边缘不规则的手裁圆片
  5. 几乎无色（淡黄）的圆片
  6. 两个紧挨着的圆片
  7. 被画面边缘裁掉一半的圆片

检查三件事：
  · 能不能找到
  · 测出的 RGB 准不准（会不会被背景污染）
  · 分割出来的形状圆不圆
"""
import os, sys, math, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

from detector import DetectConfig, detect_image

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_round_test")
OUT_PNG = os.path.join(TMP, "圆形纸片.jpg")


def disc(draw, cx, cy, r, color, irregular=0.0, seed=0, angle=0.0):
    """画一个（可带不规则边缘的）圆片，返回它覆盖的像素"""
    rng = np.random.RandomState(seed)
    pts = []
    n = 96
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1.0 + irregular * (rng.rand() - 0.5) * 2)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    if angle:
        ca, sa = math.cos(angle), math.sin(angle)
        pts = [(cx + (x - cx) * ca - (y - cy) * sa,
                cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]
    draw.polygon(pts, fill=color)
    return pts


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)

    W, H = 3200, 2100
    img = Image.new("RGB", (W, H), (241, 240, 238))
    d = ImageDraw.Draw(img)

    # 背景纹理 + 一把尺子（深色刻度线，用来考验会不会把刻度误当滤纸片）
    for i in range(0, H, 6):
        d.line([(0, i), (W, i)], fill=(238, 237, 235), width=1)
    d.rectangle([0, 1500, W, 1760], fill=(236, 234, 230))
    for x in range(20, W, 55):
        d.line([(x, 1500), (x, 1560)], fill=(70, 70, 70), width=3)
        d.line([(x, 1500), (x, 1530)], fill=(110, 110, 110), width=2)
    d.text((60, 1620), "0    1    2    3    4    5    6    7    8    9", fill=(40, 40, 40))

    # 手写标注
    d.text((120, 180), "0.001", fill=(35, 35, 35))
    d.text((700, 180), "0.002", fill=(35, 35, 35))
    d.text((1300, 180), "0.003", fill=(35, 35, 35))

    specs = []
    # (名称, 圆心, 半径, 颜色, 不规则度, 旋转)
    specs.append(("大圆片", (380, 620), 210, (214, 192, 92), 0.0, 0))
    specs.append(("中等圆片", (900, 560), 145, (198, 176, 108), 0.0, 0))
    specs.append(("小圆片", (1290, 600), 78, (176, 158, 126), 0.0, 0))
    specs.append(("手裁不规则圆", (1620, 590), 150, (206, 186, 104), 0.14, 0.4))
    specs.append(("几乎无色圆片", (2010, 620), 130, (226, 221, 206), 0.0, 0))
    specs.append(("紧挨的圆A", (2530, 620), 140, (222, 206, 130), 0.0, 0))
    specs.append(("紧挨的圆B", (2790, 620), 140, (206, 190, 118), 0.0, 0))
    specs.append(("被裁掉一半", (3190, 900), 170, (194, 172, 110), 0.0, 0))

    for name, (cx, cy), r, col, irr, ang in specs:
        disc(d, cx, cy, r, col, irr, seed=hash(name) % 1000, angle=ang)

    img.save(OUT_PNG, quality=94)

    cfg = DetectConfig()
    res = detect_image(OUT_PNG, cfg)
    # 说明：「紧挨的圆A / 紧挨的圆B」故意画成了互相重叠，
    # 它们在图像上是一个连通区域，程序只能测出合并后的平均值，
    # 所以独立的区域数是 7 而不是 8。
    print(f"照片里放了 {len(specs)} 片圆片（其中 2 片互相重叠），"
          f"识别到 {res.n} 个独立区域\n")
    print(f"{'名称':<14}{'R':>7}{'G':>7}{'B':>7}{'设定值':>18}{'偏差':>7}"
          f"{'占框%':>7}{'圆度':>7}")
    print("-" * 84)

    ok = True
    for d_ in res.detections:
        cx = (d_.bbox[0] + d_.bbox[2]) / 2
        cy = (d_.bbox[1] + d_.bbox[3]) / 2
        best = min(specs, key=lambda s: abs(s[1][0] - cx) + abs(s[1][1] - cy))
        want = best[3]
        got = (d_.rgb_mean[0], d_.rgb_mean[1], d_.rgb_mean[2])
        dev = max(abs(got[i] - want[i]) for i in range(3))
        bw = d_.bbox[2] - d_.bbox[0]
        bh = d_.bbox[3] - d_.bbox[1]
        # 圆度：真实圆片 面积/外接框面积 ≈ π/4 ≈ 0.785
        round_ = d_.paper_area_px / max(1, bw * bh)
        flag = "✓" if dev < 14 else "✗"
        if dev >= 14:
            ok = False
        print(f"{best[0]:<14}{got[0]:>7.1f}{got[1]:>7.1f}{got[2]:>7.1f}"
              f"{str(want):>18}{dev:>7.1f}{d_.paper_ratio*100:>6.0f}%"
              f"{round_:>7.2f}  {flag}")

    print("\n圆度参考：正圆 = 0.785（分割面积/外接框面积）")
    print("结论：", "圆形纸片全部识别 ✓" if ok and res.n == 7
          else f"存在问题 ✗ (识别 {res.n}/7)")
    print("图已保存:", OUT_PNG)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
