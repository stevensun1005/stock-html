#!/usr/bin/env python3
"""verify.py — 用无头 Chrome 真正渲染页面，读出页面内置自检的结果，并可分段截图。

    python3 verify.py page.html                 # 只跑自检：两个主题都 PASS 才算过
    python3 verify.py page.html --shots shots/  # 再把页面按屏切片截图（浅色 + 深色）
    python3 verify.py page.html --shots shots/ --full   # 另存整页长图
    python3 verify.py page.html --shots shots/ --at paths,risks,c3   # 只截某几节（按小节 id，高度自动）

退出码：0 = PASS,1 = FAIL,2 = 找不到浏览器（改用下面的备用办法）。
找不到 Chrome / Chromium / Edge 时：设环境变量 CHROME=/path/to/chrome,
或者直接在任何浏览器里打开  page.html?check=1  看底部的检查条 / 控制台里的 [CHECK ...]。
只依赖 Python 标准库。
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CANDIDATES = [
    os.environ.get("CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    for c in CANDIDATES:
        if not c:
            continue
        if os.path.isfile(c):
            return c
        w = shutil.which(c)
        if w:
            return w
    return None


def run(browser, profile, url, extra, timeout=90):
    cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
           "--disable-extensions", "--user-data-dir=" + profile, "--virtual-time-budget=8000"] + extra + [url]
    # 显式 UTF-8：Windows 中文系统默认按 GBK 解码，Chrome 输出的 UTF-8 DOM 会让读取线程崩掉
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def main():
    for stream in (sys.stdout, sys.stderr):  # 控制台编码不是 UTF-8 时也别因为打印中文而崩
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("--shots", help="截图输出目录")
    ap.add_argument("--full", action="store_true", help="另存整页长图 full-<theme>.png")
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--slice", type=int, default=0, help="slice height in px (default 1300; with --at, the section's own height)")
    ap.add_argument("--scale", type=float, default=1.0, help="设备像素比；做 README 配图可用 2")
    ap.add_argument("--themes", default="light,dark")
    ap.add_argument("--at", help="只截指定小节（逗号分隔的 id，如 mainline,c3,paths,risks），不切整页")
    a = ap.parse_args()

    page = Path(a.page).resolve()
    if not page.is_file():
        sys.exit("找不到文件：%s" % page)
    browser = find_browser()
    if not browser:
        print("找不到 Chrome / Chromium / Edge。备用办法：在浏览器里打开 %s?check=1 看底部检查条。" % page.as_uri())
        sys.exit(2)

    profile = tempfile.mkdtemp(prefix="stock-html-")
    try:
        r = run(browser, profile, page.as_uri() + "?check=1", ["--window-size=%d,1200" % a.width, "--dump-dom"])
        m = re.search(r'<pre id="stock-html-check"[^>]*>(.*?)</pre>', r.stdout or "", re.S)
        if not m:
            print("页面里没读到自检结果（是不是没用 assets/template.html 的脚本？）\n" + (r.stderr or "")[-600:])
            sys.exit(1)
        import html as _html
        res = json.loads(_html.unescape(m.group(1)))
        ok = True
        for theme, t in res["themes"].items():
            n = sum(len(v) for v in t["issues"].values())
            print("[CHECK %s] %s" % (theme, "PASS" if t["pass"] else "FAIL — %d 处" % n))
            ok = ok and t["pass"]
        if not ok:
            for kind, items in res["themes"]["light"]["issues"].items():
                for it in items:
                    print("   %-8s %s" % (kind, it))
        print("svg: %d   page height: %dpx" % (res["svgs"], res["height"]))

        if a.shots:
            out = Path(a.shots).resolve()  # Chrome 的 --screenshot 不认相对路径（工作目录不同）
            out.mkdir(parents=True, exist_ok=True)
            sl = a.slice or 1300
            n = math.ceil((res["height"] + 40) / sl)
            sc = ["--force-device-scale-factor=%g" % a.scale]
            if a.at:
                for theme in a.themes.split(","):
                    for sid in a.at.split(","):
                        f = out / ("%s-%s.png" % (theme, sid))
                        hh = a.slice or min(res.get("sections", {}).get(sid, 1300) + 30, 6000)
                        run(browser, profile, "%s?theme=%s&at=%s" % (page.as_uri(), theme, sid),
                            sc + ["--window-size=%d,%d" % (a.width, hh), "--screenshot=%s" % f])
                print("截图：%s  （%s）" % (out, a.at))
                sys.exit(0 if ok else 1)
            for theme in a.themes.split(","):
                for k in range(n):
                    f = out / ("%s-%02d.png" % (theme, k + 1))
                    run(browser, profile, "%s?theme=%s&slice=%d&sliceh=%d" % (page.as_uri(), theme, k, sl),
                        sc + ["--window-size=%d,%d" % (a.width, sl), "--screenshot=%s" % f])
                if a.full:
                    f = out / ("full-%s.png" % theme)
                    run(browser, profile, "%s?theme=%s" % (page.as_uri(), theme),
                        sc + ["--window-size=%d,%d" % (a.width, res["height"] + 40), "--screenshot=%s" % f])
            print("截图：%s  （%d 张切片 × %d 个主题%s）" % (out, n, len(a.themes.split(",")), "，外加整页长图" if a.full else ""))
            print("逐张看图：文字压线 / 标签挤在一起 / 图例被撑大 / 印章被遮 / 英文副标题断行 / 色带里的字重叠。")
        sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
