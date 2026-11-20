# -*- coding: utf-8 -*-
"""端到端自检：识别 → 校验 → 导出 CSV/Excel → 总览图 → 存档"""
import os, sys, time, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

import app as A
from detector import DetectConfig, detect_image, list_images, measure_region, normalize_rgb

ROOT = r"E:\枸杞各组分道地性\显色反应\all_pics"
OUT = r"E:\枸杞各组分道地性\显色反应\_preview"


def main():
    ok = True
    os.makedirs(OUT, exist_ok=True)

    # ---------- 1. 基本识别 ----------
    cfg = DetectConfig()
    t0 = time.time()
    files = list_images(ROOT)
    results = [detect_image(f, cfg) for f in files]
    print(f"[1] 识别 {len(files)} 张照片，用时 {time.time()-t0:.1f}s，"
          f"共 {sum(r.n for r in results)} 片滤纸片")
    errs = [r for r in results if r.error]
    if errs:
        ok = False
        print("    !! 有照片识别出错:", [(r.name, r.error) for r in errs][:3])
    else:
        print("    ✓ 无识别错误")

    # ---------- 2. 色值合理性 ----------
    bad = []
    for r in results:
        for d in r.detections:
            R, G, B = d.rgb_mean
            if not (0 <= R <= 255 and 0 <= G <= 255 and 0 <= B <= 255):
                bad.append((r.name, d.index, "RGB 越界"))
            if d.area_px <= 0:
                bad.append((r.name, d.index, "面积为 0"))
            Lv, Av, Bv = d.lab
            if not (0 <= Lv <= 100):
                bad.append((r.name, d.index, f"L*={Lv}"))
    print("[2] 色值合理性:", "✓ 全部通过" if not bad else f"✗ {bad[:5]}")
    ok &= not bad

    # ---------- 3. 手动测量 ----------
    r0 = results[0]
    d0 = r0.detections[0]
    m = measure_region(r0.path, d0.bbox, cfg)
    print(f"[3] 手动测量: 自动({d0.rgb_mean[0]:.1f},{d0.rgb_mean[1]:.1f},{d0.rgb_mean[2]:.1f})"
          f"  手动({m.rgb_mean[0]:.1f},{m.rgb_mean[1]:.1f},{m.rgb_mean[2]:.1f})")
    diff = max(abs(a - b) for a, b in zip(d0.rgb_mean, m.rgb_mean))
    print(f"    最大偏差 {diff:.1f}（自动用颜色掩膜，手动用内圈，属于预期差异）")

    # ---------- 4. 白平衡归一化 ----------
    wb = normalize_rgb(d0.rgb_mean, r0.bg_rgb)
    print(f"[4] 白平衡归一化: {tuple(round(v,1) for v in d0.rgb_mean)} -> "
          f"{tuple(round(v,1) for v in wb)}  (背景 {tuple(round(v,1) for v in r0.bg_rgb)})")

    # ---------- 5. 导出 CSV / Excel ----------
    a = A.App()
    a.withdraw()
    a.dir_var.set(ROOT)
    a.results = results
    rows = a._rows()
    csv_path = os.path.join(OUT, "自检_导出.csv")
    xlsx_path = os.path.join(OUT, "自检_导出.xlsx")
    a._write_export(csv_path, rows, "csv")
    a._write_export(xlsx_path, rows, "xlsx")
    with open(csv_path, encoding="utf-8-sig") as f:
        rd = list(csv.DictReader(f))
    print(f"[5] 导出: CSV {len(rd)} 行 / Excel {os.path.getsize(xlsx_path)//1024} KB")
    if len(rd) != sum(r.n for r in results):
        ok = False
        print("    ✗ 行数与检测数不符")
    else:
        print("    ✓ 行数一致")

    # ---------- 6. 总览图 ----------
    from detector import make_contact_sheet
    sheet = os.path.join(OUT, "自检_总览.jpg")
    make_contact_sheet(results, sheet, cols=4, thumb=320)
    print(f"[6] 总览图: {sheet}  {os.path.getsize(sheet)//1024} KB")

    # ---------- 7. 存档读写 ----------
    a.store = {}
    a.results = [results[0]]
    a.cur = 0
    a._store_current("测试备注 0.0025 g/mL")
    a2 = A.App()
    a2.withdraw()
    rec = a2.store.get(results[0].path, {})
    good = rec.get("confirmed") and rec.get("note") == "测试备注 0.0025 g/mL" \
        and len(rec.get("detections", [])) == results[0].n
    print("[7] 存档:", "✓ 正常" if good else "✗ 异常")
    ok &= good
    # 清理测试存档
    try:
        os.remove(A.STORE_FILE)
    except Exception:
        pass
    a.destroy()
    a2.destroy()

    print("\n=== 自检", "全部通过 ✓" if ok else "存在问题 ✗", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
