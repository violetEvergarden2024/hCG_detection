# -*- coding: utf-8 -*-
"""调试脚本：对整个目录跑一遍检测，输出带框预览图 + 统计"""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detector import *

ROOT = r"E:\枸杞各组分道地性\显色反应\all_pics"
OUT = r"E:\枸杞各组分道地性\显色反应\_preview\detected"

def main():
    os.makedirs(OUT, exist_ok=True)
    cfg = DetectConfig()
    files = list_images(ROOT)
    print("图片数:", len(files))
    t0 = time.time()
    allres = []
    for i, f in enumerate(files):
        r = detect_image(f, cfg)
        allres.append(r)
        stem = "%02d_%s" % (i, os.path.splitext(os.path.basename(f))[0][:30])
        try:
            with Image.open(f) as im:
                im = im.convert("RGB")
                ov = draw_overlay(im, r.detections, max_side=1100)
                ov.save(os.path.join(OUT, stem + ".jpg"), quality=88)
        except Exception as e:
            print("  save err", e)
        print(f"[{i+1}/{len(files)}] {os.path.relpath(f, ROOT)}  -> {r.n} 片  "
              f"bg=({r.bg_a:.1f},{r.bg_b:.1f}) {r.error}")
        for d in r.detections:
            print(f"     #{d.index} bbox={d.bbox} RGB=({d.rgb_mean[0]:.1f},{d.rgb_mean[1]:.1f},{d.rgb_mean[2]:.1f})"
                  f" fill={d.fill_ratio:.2f} ax={d.axis_ratio:.2f} of={d.oriented_fill:.2f} hex={d.hex_color}")
    print("总耗时 %.1fs" % (time.time() - t0))
    tot = sum(r.n for r in allres)
    print("共检出滤纸片:", tot)

if __name__ == "__main__":
    main()
