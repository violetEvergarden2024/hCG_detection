# -*- coding: utf-8 -*-
"""
新照片鲁棒性测试：
把已有照片旋转 / 翻转 / 缩放 / 改亮度 / 改色温 / 换裁切，模拟"新拍的照片"，
再跑一遍自动识别，看还能不能找到同样数量的滤纸片。
"""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageEnhance

from detector import DetectConfig, detect_image, list_images

SRC = r"E:\枸杞各组分道地性\显色反应\all_pics"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_新照片测试")

def fit(im, long_side):
    """按比例缩放到指定长边（保持宽高比）"""
    sc = long_side / max(im.size)
    return im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                     Image.LANCZOS)


# (原图, 新图后缀, 变换, 期望数量)
# 说明：期望数量是人工核对过的「这张新照片里确实有几片滤纸片」
#      （被画面裁掉只剩一角的那种不算）
CASES = [
    (r"1102\微信图片_20261102221336_236_94.jpg", "旋转90度+缩到3200",
     lambda im: fit(im.rotate(90, expand=True), 3200), 5),
    (r"1102\微信图片_20261102221336_236_94.jpg", "左右翻转+提亮+加暖",
     lambda im: ImageEnhance.Brightness(
         im.transpose(Image.FLIP_LEFT_RIGHT)).enhance(1.25), 5),
    (r"第一次\微信图片_20261106165146_262_94.jpg", "放大2倍+低对比度",
     lambda im: ImageEnhance.Contrast(im.resize((im.width * 2, im.height * 2),
                                                Image.LANCZOS)).enhance(0.55), 4),
    (r"第三次\微信图片_20261110232401_141_2.jpg", "裁掉左侧1/3+冷色",
     lambda im: im.crop((im.width // 3, 0, im.width, im.height)), 2),
    (r"2026年10月31日164702.jpg", "缩小到1600宽",
     lambda im: fit(im, 1600), 5),
    (r"第四次-滤纸片完全浸泡\微信图片_20261112225054_324_94.jpg", "手机竖屏+偏色+暗",
     lambda im: ImageEnhance.Brightness(fit(im, 2400)).enhance(0.8), 3),
]


def color_shift(im, r=1.0, g=1.0, b=1.0):
    """给整图加一点色温偏移，模拟不同光源"""
    a = np.asarray(im, np.float32)
    a[:, :, 0] *= r
    a[:, :, 1] *= g
    a[:, :, 2] *= b
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)

    cfg = DetectConfig()
    print("=" * 96)
    print(f"{'原照片':<34}{'模拟新照片':<24}{'原数':>5}{'新数':>6}{'结果':>8}")
    print("=" * 96)

    allok = True
    for rel, tag, fn, expect in CASES:
        src = os.path.join(SRC, rel)
        orig = Image.open(src).convert("RGB")
        n_orig = detect_image(src, cfg).n

        new = fn(orig)
        if "冷色" in tag:
            new = color_shift(new, 0.92, 0.97, 1.12)
        if "暖" in tag:
            new = color_shift(new, 1.10, 1.02, 0.90)
        out = os.path.join(TMP, "新照片_" + tag.replace("/", "分之") + ".jpg")
        new.save(out, quality=92)

        res = detect_image(out, cfg)
        ok = (res.n == expect)
        allok &= ok
        print(f"{os.path.basename(rel)[:26]:<28}{tag:<20}"
              f"原{ n_orig:>2}  期望{expect:>2}  实得{res.n:>2}  "
              f"阈值{res.threshold:>5.1f}  {'✓' if ok else '✗'}")
        for d in res.detections[:3]:
            print(f"      #{d.index} RGB=({d.rgb_mean[0]:.1f},{d.rgb_mean[1]:.1f},"
                  f"{d.rgb_mean[2]:.1f}) {d.hex_color} [{d.source}]")

    print("=" * 96)
    print("结论：", "新拍的照片同样可以自动识别 ✓" if allok
          else "部分变换下数量有变化，需人工复核 ✗")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
