# -*- coding: utf-8 -*-
"""扫参数：不同阈值阶梯 + 打分权重，在「原 46 张」与「模拟新照片」上的表现"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageEnhance

from detector import DetectConfig, detect_image, list_images

SRC = r"E:\枸杞各组分道地性\显色反应\all_pics"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_sweep")


def fit(im, long_side):
    sc = long_side / max(im.size)
    return im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)


def build_new():
    os.makedirs(TMP, exist_ok=True)
    jobs = []
    specs = [
        (r"1102\微信图片_20261102221336_236_94.jpg", "rot",
         lambda im: fit(im.rotate(90, expand=True), 3200), 6),
        (r"1102\微信图片_20261102221336_236_94.jpg", "bright",
         lambda im: ImageEnhance.Brightness(
             im.transpose(Image.FLIP_LEFT_RIGHT)).enhance(1.25), 6),
        (r"第一次\微信图片_20261106165146_262_94.jpg", "flat",
         lambda im: ImageEnhance.Contrast(im.resize((im.width * 2, im.height * 2),
                                                    Image.LANCZOS)).enhance(0.55), 4),
        (r"第三次\微信图片_20261110232401_141_2.jpg", "crop",
         lambda im: im.crop((im.width // 3, 0, im.width, im.height)), 2),
        (r"2026年10月31日164702.jpg", "small",
         lambda im: fit(im, 1600), 5),
        (r"第四次-滤纸片完全浸泡\微信图片_20261112225054_324_94.jpg", "dim",
         lambda im: ImageEnhance.Brightness(fit(im, 2400)).enhance(0.8), 3),
    ]
    for rel, tag, fn, exp in specs:
        im = Image.open(os.path.join(SRC, rel)).convert("RGB")
        new = fn(im)
        if tag == "crop":
            a = np.asarray(new, np.float32); a[:, :, 0] *= 0.92
            a[:, :, 1] *= 0.97; a[:, :, 2] *= 1.12
            new = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        p = os.path.join(TMP, tag + ".jpg")
        new.save(p, quality=92)
        jobs.append((p, exp, tag))
    return jobs


def _w(a):
    path, cfg = a
    return detect_image(path, cfg).n


def main():
    jobs = build_new()
    files = list_images(SRC)
    combos = []
    for lad in [(1.0, 1.4, 2.0, 2.8, 3.8, 5.2, 7.0, 10.0),
                (0.6, 1.0, 1.4, 2.0, 2.8, 3.8, 5.2, 7.0, 10.0)]:
        for w in (0.0, 0.2, 0.5):
            combos.append((lad, w))
    for lad, w in combos:
        cfg = DetectConfig(threshold_ladder=lad, score_small_weight=w)
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=8) as ex:
            n_orig = list(ex.map(_w, [(f, cfg) for f in files]))
        with ProcessPoolExecutor(max_workers=6) as ex:
            n_new = list(ex.map(_w, [(p, cfg) for p, e, t in jobs]))
        tot = sum(n_orig)
        line = " ".join(f"{t}:{n}/{e}" for (p, e, t), n in zip(jobs, n_new))
        print(f"阶梯起{lad[0]:>4} 权重{w:>4}: 原图 {tot:>3} 片 | {line} | {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
