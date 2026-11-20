# -*- coding: utf-8 -*-
"""自动启动识别并截图，用于验证界面"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from PIL import ImageGrab
import app as A

OUT = r"E:\枸杞各组分道地性\显色反应\_preview"


def main():
    a = A.App()
    a.geometry("1600x980+40+40")
    a.attributes("-topmost", True)
    a.update()
    a.lift()
    a.focus_force()

    def shoot(path):
        time.sleep(0.8)
        a.update()
        img = ImageGrab.grab()
        img.save(path)
        print("saved", path, img.size)

    shoot(os.path.join(OUT, "ui_0_start.png"))

    a.start_scan()
    t0 = time.time()
    while a.busy and time.time() - t0 < 600:
        a.update()
        time.sleep(0.3)
    a.update()
    time.sleep(0.5)
    a.update()
    print("扫描耗时 %.1f 秒" % (time.time() - t0))
    shoot(os.path.join(OUT, "ui_1_done.png"))

    if a.results:
        r = a.results[6]
        a.file_tree.selection_set(r.path)
        a.file_tree.focus(r.path)
        a.on_file_select()
        a.update()
        time.sleep(0.3)
        a.update()
        if r.detections:
            a.sel_det = r.detections[min(1, len(r.detections) - 1)].index
            a.det_tree.selection_set(str(a.sel_det))
            a.on_det_select()
            a.redraw()
        a.update()
        time.sleep(0.5)
        a.update()
        shoot(os.path.join(OUT, "ui_2_selected.png"))
        print("选中的照片:", r.name, "检测数:", r.n)

    if a.results:
        a.zoom_mode = "free"
        a.zoom = 0.42
        a.redraw()
        a.update()
        time.sleep(0.4)
        a.update()
        shoot(os.path.join(OUT, "ui_3_zoom.png"))

    print("状态:", a.status_var.get())
    a.destroy()


if __name__ == "__main__":
    main()
