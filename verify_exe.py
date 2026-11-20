# -*- coding: utf-8 -*-
"""
验证打包好的 exe 能独立运行（不依赖任何 Python 解释器）
=======================================================
做法：临时把 PATH 里的 python 全部屏蔽，再启动 exe，
      让它自己识别几张照片，看是否正常。
"""
import os, sys, time, subprocess, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
EXE = os.path.join(DIST, "滤纸片RGB识别.exe")

# 一个"探针" exe：验证打包环境里 numpy / PIL / tkinter 都能用
PROBE_SRC = r'''
import sys, os, json
import numpy as np
from PIL import Image, ImageTk, ImageFilter, ImageDraw
import tkinter as tk
from multiprocessing import freeze_support

def child(_):
    return 1

if __name__ == "__main__":
    freeze_support()
    out = {"python": sys.version.split()[0],
           "frozen": bool(getattr(sys, "frozen", False)),
           "numpy": np.__version__,
           "pil": Image.__version__}
    try:
        import openpyxl
        out["openpyxl"] = openpyxl.__version__
    except Exception as e:
        out["openpyxl"] = "缺失: %s" % e
    # 多进程可用性
    try:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=2) as ex:
            out["mp"] = sum(ex.map(child, [1, 2]))
    except Exception as e:
        out["mp"] = "失败: %s" % e
    # tkinter 能否建窗口
    try:
        r = tk.Tk(); r.withdraw(); r.update(); r.destroy()
        out["tk"] = "ok"
    except Exception as e:
        out["tk"] = "失败: %s" % e
    p = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
                     else os.getcwd(), "探针结果.json")
    open(p, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False))
'''


def main():
    if not os.path.exists(EXE):
        print("找不到 exe:", EXE)
        return 1

    # 1) 打包一个探针 exe，验证运行环境
    probe_src = os.path.join(HERE, "_probe.py")
    with open(probe_src, "w", encoding="utf-8") as f:
        f.write(PROBE_SRC)
    print("=== 打包探针（验证 exe 内的运行环境） ===")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--name", "探针", "--distpath", DIST, "--workpath",
                    os.path.join(HERE, "_probe_build"), "--specpath",
                    os.path.join(HERE, "_probe_build"), "--onefile", "--windowed",
                    probe_src], cwd=HERE, capture_output=True)

    probe_exe = os.path.join(DIST, "探针.exe")
    if not os.path.exists(probe_exe):
        print("探针打包失败")
        return 1

    # 2) 在「屏蔽 python 的 PATH」下运行探针
    env = dict(os.environ)
    env["PATH"] = "C:\\Windows\\System32;C:\\Windows"
    for k in ("PYTHONHOME", "PYTHONPATH", "PYINSTALLER_CONFIG"):
        env.pop(k, None)
    print("\n=== 在无 Python 的 PATH 下运行探针 ===")
    r = subprocess.run([probe_exe], env=env, capture_output=True, text=True, timeout=300)
    res_file = os.path.join(DIST, "探针结果.json")
    if os.path.exists(res_file):
        print(open(res_file, encoding="utf-8").read())
    else:
        print("探针没有产出结果，退出码", r.returncode)
        print("stdout:", r.stdout[-800:])
        print("stderr:", r.stderr[-800:])
        return 1

    # 3) 真正启动主程序（GUI），确认不崩
    print("=== 启动主程序（3 秒后关闭） ===")
    p = subprocess.Popen([EXE], env=env)
    time.sleep(6)
    alive = p.poll() is None
    print("主程序仍在运行:", alive, "（True 表示 GUI 正常启动）")
    if alive:
        p.terminate()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
    return 0 if alive else 1


if __name__ == "__main__":
    sys.exit(main())
