# -*- coding: utf-8 -*-
"""扫相对面积下限 rel_area_ratio：看它对「大小不一的滤纸片」的影响"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concurrent.futures import ProcessPoolExecutor
from detector import DetectConfig, detect_image, list_images

SRC = r"E:\枸杞各组分道地性\显色反应\all_pics"
ROUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_round_test", "圆形纸片.jpg")


def _w(a):
    path, rel = a
    cfg = DetectConfig(rel_area_ratio=rel)
    r = detect_image(path, cfg)
    return r.n


def main():
    files = list_images(SRC)
    print(f"{'rel_area_ratio':>16}{'实拍46张':>10}{'圆形测试图':>12}")
    for rel in (0.18, 0.12, 0.08, 0.06, 0.04, 0.02):
        with ProcessPoolExecutor(max_workers=8) as ex:
            n1 = list(ex.map(_w, [(f, rel) for f in files]))
        n2 = detect_image(ROUND, DetectConfig(rel_area_ratio=rel)).n
        print(f"{rel:>16}{sum(n1):>10}{n2:>10}")


if __name__ == "__main__":
    main()
