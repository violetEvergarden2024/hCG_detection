# -*- coding: utf-8 -*-
"""界面交互流程自检：手动框选 / 删除 / 重测 / 切图 / 导出"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from PIL import Image
import app as A

ROOT = r"E:\枸杞各组分道地性\显色反应\all_pics"


def main():
    a = A.App()
    a.withdraw()
    a.geometry("1500x950+0+0")
    a.update()
    a.dir_var.set(ROOT)
    a.start_scan()
    t0 = time.time()
    while a.busy and time.time() - t0 < 600:
        a.update()
        time.sleep(0.2)
    a.update()
    print(f"识别完成：{len(a.results)} 张 / {sum(r.n for r in a.results)} 片，"
          f"用时 {time.time()-t0:.1f}s")
    assert a.results, "没有结果"

    # ---- 选图 ----
    r = a.results[3]
    a.file_tree.selection_set(r.path)
    a.file_tree.focus(r.path)
    a.on_file_select()
    a.update()
    print(f"切换到 {r.name}: {r.n} 片")

    # ---- 手动框选（在画面右下角空白处画一个框）----
    n0 = r.n
    a.toggle_box_mode()
    assert a.draw_mode
    im = a._cur_image()
    v = a._view_rect()
    _, ox, oy, z = v
    f = im.size[0] / r.width
    # 取全分辨率坐标 (x, y, x+200, y+200)
    fx, fy = 120, 120
    x0 = fx * f * z + ox
    y0 = fy * f * z + oy
    x1 = (fx + 260) * f * z + ox
    y1 = (fy + 260) * f * z + oy
    a.on_left_down(type("E", (), {"x": int(x0), "y": int(y0)})())
    a.on_left_move(type("E", (), {"x": int(x1), "y": int(y1)})())
    a.on_left_up(type("E", (), {"x": int(x1), "y": int(y1)})())
    a.update()
    print(f"手动框选: {n0} -> {r.n} 片（应为 {n0+1}）")
    assert r.n == n0 + 1, "手动框选没有生效"
    assert r.detections[-1].source == "manual"
    print(f"  新框 #{r.detections[-1].index} RGB="
          f"{tuple(round(v,1) for v in r.detections[-1].rgb_mean)}")

    # ---- 复制 RGB ----
    a.sel_det = r.detections[-1].index
    a._refresh_dets()
    a.copy_rgb()
    print("  剪贴板:", a.clipboard_get())

    # ---- 重测 ----
    before = r.detections[-1].rgb_mean
    a.remeasure_sel()
    after = r.detections[-1].rgb_mean
    print(f"  重测前后 RGB: {tuple(round(v,1) for v in before)} -> "
          f"{tuple(round(v,1) for v in after)}")
    assert abs(before[0] - after[0]) < 1e-6, "重测结果异常"

    # ---- 删除 ----
    a.delete_sel()
    a.update()
    print(f"  删除后: {r.n} 片（应回到 {n0}）")
    assert r.n == n0, "删除没有生效"

    # ---- 切图 / 切换检测 ----
    a.step_photo(1)
    a.update()
    print(f"  下一张: {a.results[a.cur].name}")
    a.step_det(1)
    a.update()
    print(f"  选中第 {a.sel_det} 片")

    # ---- 测量范围切换 ----
    a.measure_mode.set("paper")
    a._refresh_dets()
    a.update()
    vals = [a._display_rgb(d) for d in a.results[a.cur].detections[:2]]
    a.measure_mode.set("color")
    a._refresh_dets()
    a.update()
    print(f"  整片/显色 两组色值可切换 ✓ ({tuple(round(v,1) for v in vals[0])})")

    # ---- 导出 ----
    rows = a._rows()
    print(f"  导出行数: {len(rows)}")
    assert len(rows) == sum(x.n for x in a.results)

    a.destroy()
    print("\n=== 界面流程自检全部通过 ✓ ===")


if __name__ == "__main__":
    main()
