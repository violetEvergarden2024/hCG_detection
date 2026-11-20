# -*- coding: utf-8 -*-
"""同时扫 rel_area_ratio 与 min_area_ratio：
目标是「实拍 46 张不多不少 + 圆形测试图里的小圆片也能找到」"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concurrent.futures import ProcessPoolExecutor
from detector import DetectConfig, detect_image, list_images

SRC = r"E:\枸杞各组分道地性\显色反应\all_pics"
ROUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_round_test", "圆形纸片.jpg")


def _w(a):
    path, rel, mini = a
    return detect_image(path, DetectConfig(rel_area_ratio=rel,
                                           min_area_ratio=mini)).n


def main():
    files = list_images(SRC)
    print(f"{'rel':>6}{'min':>9}{'实拍46张':>10}{'圆形图':>8}   备注")
    for rel in (0.18, 0.12, 0.10, 0.08):
        for mini in (0.00004, 0.0005, 0.001, 0.0015, 0.002):
            with ProcessPoolExecutor(max_workers=8) as ex:
                n1 = list(ex.map(_w, [(f, rel, mini) for f in files]))
            n2 = detect_image(ROUND, DetectConfig(rel_area_ratio=rel,
                                                  min_area_ratio=mini)).n
            print(f"{rel:>6}{mini:>9}{sum(n1):>10}{n2:>8}")


if __name__ == "__main__":
    main()
