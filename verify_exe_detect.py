# -*- coding: utf-8 -*-
"""
端到端验证打包好的 exe：
把 app.py 的识别流程塞进一个「无窗口的批处理版」，
打包成 exe，在屏蔽 Python 的 PATH 下跑一遍真实照片，
确认 exe 的识别结果和用 Python 直接跑完全一致。
"""
import os, sys, json, subprocess, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
BATCH_SRC = r'''
# -*- coding: utf-8 -*-
"""批处理版：不做 GUI，只跑识别并把结果写成 JSON（用于验证 exe）"""
import os, sys, json, multiprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concurrent.futures import ProcessPoolExecutor
from detector import DetectConfig, detect_image, list_images

def _w(a):
    p, cfg = a
    r = detect_image(p, cfg)
    return [dict(idx=d.index, bbox=list(d.bbox), src=d.source,
                 rgb=[round(v, 2) for v in d.rgb_mean],
                 paper=[round(v, 2) for v in d.rgb_paper],
                 ratio=round(d.paper_ratio, 4),
                 contour=len(d.contour)) for d in r.detections]

if __name__ == "__main__":
    multiprocessing.freeze_support()
    folder = sys.argv[1]
    outp = sys.argv[2]
    cfg = DetectConfig()
    files = list_images(folder)
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        res = list(ex.map(_w, [(f, cfg) for f in files]))
    json.dump({"n_files": len(files), "n_papers": sum(len(x) for x in res),
               "per_file": res},
              open(outp, "w", encoding="utf-8"), ensure_ascii=False)
    print("done", len(files), sum(len(x) for x in res))
'''


def main():
    src = os.path.join(HERE, "_batch.py")
    with open(src, "w", encoding="utf-8") as f:
        f.write(BATCH_SRC)
    print("=== 打包批处理 exe ===")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--name", "批处理验证", "--distpath", DIST, "--workpath",
                    os.path.join(HERE, "_batch_build"), "--specpath",
                    os.path.join(HERE, "_batch_build"), "--onefile", "--console",
                    "--paths", HERE, src], cwd=HERE, capture_output=True)

    exe = os.path.join(DIST, "批处理验证.exe")
    if not os.path.exists(exe):
        print("批处理 exe 打包失败")
        return 1

    env = dict(os.environ)
    env["PATH"] = "C:\\Windows\\System32;C:\\Windows"
    for k in ("PYTHONHOME", "PYTHONPATH"):
        env.pop(k, None)

    folder = r"E:\枸杞各组分道地性\显色反应\all_pics"
    out_exe = os.path.join(DIST, "exe结果.json")
    print("\n=== 用 exe 识别全部照片（无 Python 环境） ===")
    r = subprocess.run([exe, folder, out_exe], env=env, capture_output=True,
                       text=True, timeout=1800)
    print("stdout:", r.stdout.strip()[-300:])
    if r.returncode != 0:
        print("stderr:", r.stderr[-1500:])
        return 1
    if not os.path.exists(out_exe):
        print("没有产出结果文件")
        return 1
    exe_res = json.load(open(out_exe, encoding="utf-8"))

    print("\n=== 用 Python 直接跑（对照） ===")
    out_py = os.path.join(DIST, "py结果.json")
    sys.path.insert(0, HERE)
    from detector import DetectConfig, detect_image, list_images
    cfg = DetectConfig()
    files = list_images(folder)
    py_res = []
    for f in files:
        rr = detect_image(f, cfg)
        py_res.append([dict(idx=d.index, bbox=list(d.bbox), src=d.source,
                            rgb=[round(v, 2) for v in d.rgb_mean],
                            paper=[round(v, 2) for v in d.rgb_paper],
                            ratio=round(d.paper_ratio, 4),
                            contour=len(d.contour)) for d in rr.detections])

    print(f"exe : {exe_res['n_files']} 张, {exe_res['n_papers']} 片")
    print(f"py  : {len(py_res)} 张, {sum(len(x) for x in py_res)} 片")
    same = exe_res["per_file"] == py_res
    print("\n逐片结果完全一致:", "✓ 是" if same else "✗ 否")
    if not same:
        for i, (a, b) in enumerate(zip(exe_res["per_file"], py_res)):
            if a != b:
                print("  第", i, "个文件不同")
                print("   exe:", json.dumps(a, ensure_ascii=False)[:400])
                print("   py :", json.dumps(b, ensure_ascii=False)[:400])
                break
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
