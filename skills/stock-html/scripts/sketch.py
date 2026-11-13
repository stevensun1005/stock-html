#!/usr/bin/env python3
"""sketch.py — stock-html 的手绘图解工具箱（只依赖 Python 标准库）。

用法：在你自己的 build 脚本里
    import sys; sys.path.insert(0, "<skill 目录>/scripts")
    from sketch import *
然后用 Page / Comic / Canvas 和几个现成图表拼出整页，最后 page.save("out.html")。
save() 会先做一遍离线版面检查(文字越界 / 互相重叠 / 压漫画格边框 / 说明超字数 /
正文超 4 句 / 代价留空 / 链接未核实)，有问题直接列出来。

约定（和 SKILL.md 一致）：
  * 图形进抖动滤镜组，文字单独一组，永不加 filter / transform。
  * 颜色只用语义名：ink ink2 green orange blue red purple。
      green = 正在进行   orange = 新来的   blue = 存起来的   red(虚线)= 作废/被释放
  * fill 写颜色名 = 浅色填充；加 "!" = 实心（如 "green!"）；"card"/"paper"/"hl" = 底色。
完整示例见 ../examples/boba_merger.py。
"""
import html
import json
import math
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # 控制台不是 UTF-8（如 Windows GBK）时，打印 ¥ 等字符也别崩
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(errors="replace")
        except (ValueError, OSError):
            pass

__all__ = ["Canvas", "Comic", "Page", "Stop", "snake", "metro", "paths_chart", "ruler_chart",
           "waterfall", "timeline", "roadmap", "risk_matrix", "set_lang", "text_w", "LABELS"]

REPO_URL = "https://github.com/stevensun1005/stock-html"

LABELS = {
    "zh": dict(
        html_lang="zh-CN", capmax=15, kicker="图解 · 一遍看懂",
        pain="烦恼", fix="办法", solves="解决了什么：", cost="代价是什么：",
        stamps=["下一站", "补一下", "已学"], toDark="● 黑板", toLight="○ 方格纸",
        brings="带来：", today="今天", prob_note="概率为主观估计，不是预测",
        mainline="主线", checkup="体检单", chain="概念依赖链", cards="逐个概念：两格漫画",
        chain_note="后一个概念，是为了解决前一个概念带来的问题。",
        progress="已学 <b id=\"progN\">0</b> / {m} · 点卡片右上角的印章切换进度，浏览器会记住",
        route="一遍过完：学习路线", why="为什么去：", time="去多久：", search="（需自行搜索）",
        sources="来源", disc="仅作学习用途，不构成投资建议。", made="用 stock-html 生成",
        total="合计", start="起点", subjective="位置为主观估计", focus="先盯这里", low="低", high="高",
        likely="发生的可能", impact="一旦发生的杀伤力",
        legend=[("green", "正在进行（业务、利润）"), ("orange", "新来的（新事件、新股东）"),
                ("blue", "存起来的（股份、现金）"), ("red", "作废 / 被释放的")],
    ),
    "en": dict(
        html_lang="en", capmax=32, kicker="Explained · ELI5",
        pain="Pain", fix="Fix", solves="What it solves: ", cost="What it costs: ",
        stamps=["Next", "Review", "Done"], toDark="● Chalkboard", toLight="○ Graph paper",
        brings="brings: ", today="Today", prob_note="Probabilities are subjective, not forecasts",
        mainline="The big picture", checkup="Health check", chain="Concept chain",
        cards="Concept by concept", chain_note="Each concept exists to fix the problem the previous one created.",
        progress="Done <b id=\"progN\">0</b> / {m} · click a card's stamp to track progress",
        route="Learn it in one pass", why="Why: ", time="Time: ", search="(search for it yourself)",
        sources="Sources", disc="For learning only. Not investment advice.", made="Made with stock-html",
        total="Total", start="Start", subjective="Positions are subjective", focus="Watch these first",
        low="low", high="high", likely="Likelihood", impact="Damage if it happens",
        legend=[("green", "In motion (business, profit)"), ("orange", "New (events, new holders)"),
                ("blue", "Stored (shares, cash)"), ("red", "Voided / released")],
    ),
}
_LANG = "zh"


def set_lang(lang):
    """切换页面语言（"zh" / "en"）。要在创建 Comic / Page 之前调用。"""
    global _LANG
    if lang not in LABELS:
        raise ValueError("lang must be one of %s" % list(LABELS))
    _LANG = lang


def _L():
    return LABELS[_LANG]


# ------------------------------------------------------------------ 小工具
def _n(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def _esc(s):
    return html.escape(str(s), quote=True)


def _inline(s):
    """正文允许内联 HTML(<b> <mark> <code> <a>)；裸的 & 和 < 自动转义（如 M&A）。"""
    s = re.sub(r"&(?![a-zA-Z#][a-zA-Z0-9]*;)", "&amp;", str(s))
    return re.sub(r"<(?![a-zA-Z/])", "&lt;", s)


def _plain(s):
    return re.sub(r"<[^>]+>", "", str(s))


def text_w(s, size, bold=False):
    """估算一行文字的像素宽度（系统无衬线）。浏览器里的自检才是准绳，这里用于提前发现问题。"""
    w = 0.0
    for ch in str(s):
        o = ord(ch)
        if o >= 0x2E80 or ch in "“”‘’—…":
            w += 1.0
        elif ch == " ":
            w += 0.28
        elif ch in "il.,:;'|!·()[]":
            w += 0.31
        elif ch in "mwMW%":
            w += 0.86
        elif ch.isupper():
            w += 0.68
        elif ch.isdigit() or ch in "$+-=×÷<>~→":
            w += 0.6
        else:
            w += 0.54
    return w * size * (1.04 if bold else 1.0)


def _fit(s, size, maxw, bold=False, floor=11):
    while size > floor and text_w(s, size, bold) > maxw:
        size -= 0.5
    return size


def _nice(step):
    e = 10 ** math.floor(math.log10(step))
    for m in (1, 2, 2.5, 5, 10):
        if step <= m * e:
            return m * e
    return 10 * e


def _sentences(s):
    return len(re.findall(r"[\u3002\uff01\uff1f!?]|\.(?=\s|$)", _plain(s)))


class _Box:
    __slots__ = ("x0", "y0", "x1", "y1", "s", "cap")

    def __init__(self, x0, y0, x1, y1, s, cap):
        self.x0, self.y0, self.x1, self.y1, self.s, self.cap = x0, y0, x1, y1, s, cap


# ------------------------------------------------------------------ 画布
class Canvas:
    """一张内联 SVG。大图默认 760 宽；字号不要小于 12（窄屏缩放后看不清）。"""

    def __init__(self, w=760, h=300, name="figure"):
        self.w, self.h, self.name = w, h, name
        self._sh, self._tx, self.boxes, self.panels = [], [], [], []

    # ---- 图形（进抖动组）
    @staticmethod
    def _cls(stroke, fill, dash, cls):
        c = ["sh", "k-%s" % (stroke or "none")]
        if fill is None:
            c.append("f-none")
        elif fill.endswith("!"):
            c.append("fs-%s" % fill[:-1])
        else:
            c.append("f-%s" % fill)
        if dash:
            c.append("dash")
        if cls:
            c.append(cls)
        return " ".join(c)

    def rect(self, x, y, w, h, stroke="ink", fill=None, dash=False, r=8, cls=""):
        self._sh.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" class="%s"/>' % (
            _n(x), _n(y), _n(w), _n(h), _n(r), self._cls(stroke, fill, dash, cls)))
        return self

    def line(self, x1, y1, x2, y2, stroke="ink", dash=False, cls=""):
        self._sh.append('<path d="M%s %sL%s %s" class="%s"/>' % (
            _n(x1), _n(y1), _n(x2), _n(y2), self._cls(stroke, None, dash, cls)))
        return self

    @staticmethod
    def _head(x, y, ang, size):
        a, b = ang + math.radians(152), ang - math.radians(152)
        return "M%s %sL%s %sL%s %s" % (_n(x + size * math.cos(a)), _n(y + size * math.sin(a)), _n(x), _n(y),
                                       _n(x + size * math.cos(b)), _n(y + size * math.sin(b)))

    def arrow(self, x1, y1, x2, y2, stroke="ink", dash=False, head=9, cls=""):
        d = "M%s %sL%s %s" % (_n(x1), _n(y1), _n(x2), _n(y2))
        k = self._cls(stroke, None, dash, cls)
        self._sh.append('<path d="%s" class="%s"/><path d="%s" class="%s"/>' % (
            d, k, self._head(x2, y2, math.atan2(y2 - y1, x2 - x1), head), self._cls(stroke, None, False, cls)))
        return self

    def curve(self, x1, y1, x2, y2, bend=0.25, stroke="ink", dash=False, arrow=True, head=9, cls=""):
        """二次曲线箭头；bend 为正向左手侧鼓出（占长度的比例）。"""
        mx, my, dx, dy = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
        cx, cy = mx + dy * bend, my - dx * bend
        self._sh.append('<path d="M%s %sQ%s %s %s %s" class="%s"/>' % (
            _n(x1), _n(y1), _n(cx), _n(cy), _n(x2), _n(y2), self._cls(stroke, None, dash, cls)))
        if arrow:
            self._sh.append('<path d="%s" class="%s"/>' % (
                self._head(x2, y2, math.atan2(y2 - cy, x2 - cx), head), self._cls(stroke, None, False, cls)))
        return self

    def circle(self, cx, cy, r, stroke="ink", fill=None, dash=False, cls=""):
        self._sh.append('<circle cx="%s" cy="%s" r="%s" class="%s"/>' % (
            _n(cx), _n(cy), _n(r), self._cls(stroke, fill, dash, cls)))
        return self

    def path(self, d, stroke="ink", fill=None, dash=False, cls=""):
        self._sh.append('<path d="%s" class="%s"/>' % (d, self._cls(stroke, fill, dash, cls)))
        return self

    def poly(self, pts, stroke="ink", fill=None, dash=False, close=True, cls=""):
        d = "M" + "L".join("%s %s" % (_n(x), _n(y)) for x, y in pts) + ("Z" if close else "")
        return self.path(d, stroke, fill, dash, cls)

    # ---- 文字（不进抖动组，不加 transform）
    def text(self, x, y, s, size=14, anchor="middle", color="ink", bold=False, cap=False):
        s = str(s)
        w = text_w(s, size, bold)
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        self.boxes.append(_Box(x0, y - 0.86 * size, x0 + w, y + 0.14 * size, s, cap))
        cls = "c-%s" % color + (" b" if bold else "") + (" cap" if cap else "")
        self._tx.append('<text x="%s" y="%s" font-size="%s" text-anchor="%s" class="%s">%s</text>' % (
            _n(x), _n(y), _n(size), anchor, cls, _esc(s)))
        return self

    def lines(self, x, y, rows, size=14, lh=1.5, **kw):
        for i, s in enumerate(rows):
            self.text(x, y + i * size * lh, s, size=size, **kw)
        return self

    # ---- 小图标
    def tick(self, cx, cy, s=10, color="green"):
        return self.path("M%s %sL%s %sL%s %s" % (_n(cx - s), _n(cy), _n(cx - s * .3), _n(cy + s * .7),
                                                 _n(cx + s), _n(cy - s * .8)), color, cls="bold")

    def cross(self, cx, cy, s=9, color="red"):
        return self.path("M%s %sL%s %sM%s %sL%s %s" % (_n(cx - s), _n(cy - s), _n(cx + s), _n(cy + s),
                                                       _n(cx + s), _n(cy - s), _n(cx - s), _n(cy + s)), color, cls="bold")

    def minus(self, cx, cy, s=9, color="orange"):
        return self.path("M%s %sL%s %s" % (_n(cx - s), _n(cy), _n(cx + s), _n(cy)), color, cls="bold")

    def person(self, cx, top, letter="A", color="blue", mood="flat"):
        """固定角色小人：圆头（带表情）+ 梯形身体，身上写字母。占位约 30×60。mood: happy / flat / sad。"""
        self.circle(cx, top + 14, 13, "ink", color)
        self.circle(cx - 4.5, top + 11.5, 1.5, None, "ink!").circle(cx + 4.5, top + 11.5, 1.5, None, "ink!")
        my = top + 19
        q = {"happy": my + 5, "sad": my - 4.5, "flat": my}[mood]
        self.path("M%s %sQ%s %s %s %s" % (_n(cx - 5), _n(my), _n(cx), _n(q), _n(cx + 5), _n(my)), "ink", cls="thin")
        self.path("M%s %sL%s %sQ%s %s %s %sL%s %sZ" % (
            _n(cx - 14), _n(top + 60), _n(cx - 9), _n(top + 32), _n(cx), _n(top + 28), _n(cx + 9), _n(top + 32),
            _n(cx + 14), _n(top + 60)), "ink", color)
        if letter:
            self.text(cx, top + 53, letter, size=13, bold=True)
        return self

    def pie(self, cx, cy, r, slices, labels=None):
        """等分饼图。slices 是颜色名列表（一块一个）；"red" 自动画成红色虚线（作废）。labels 可给每块写字母。"""
        n = len(slices)
        for i, col in enumerate(slices):
            a0 = -math.pi / 2 + 2 * math.pi * i / n
            a1 = -math.pi / 2 + 2 * math.pi * (i + 1) / n
            d = "M%s %sL%s %sA%s %s 0 %d 1 %s %sZ" % (
                _n(cx), _n(cy), _n(cx + r * math.cos(a0)), _n(cy + r * math.sin(a0)), _n(r), _n(r),
                1 if n == 1 else 0, _n(cx + r * math.cos(a1)), _n(cy + r * math.sin(a1)))
            if n == 1:
                self.circle(cx, cy, r, "ink", col)
            else:
                self.path(d, "red" if col == "red" else "ink", col, dash=(col == "red"))
            if labels and labels[i]:
                am = (a0 + a1) / 2
                self.text(cx + r * .62 * math.cos(am), cy + r * .62 * math.sin(am) + 4.5, labels[i], size=12, bold=True)
        return self

    def coins(self, x, y, n, color="green", cols=6, r=6.5, gap=4, ghost=0, start=0):
        """一排排硬币，从 (x, y) 左上角开始；ghost = 末尾再画几枚红色虚线的（作废）。每枚占 17px 见方(r=6.5, gap=4)。

        start = 从第几个格子开始画：同一堆里要换颜色时，第二次调用传 start=已画的数量。
        """
        step = 2 * r + gap
        for i in range(n + ghost):
            rr, cc = divmod(i + start, cols)
            g = i >= n
            self.circle(x + r + cc * step, y + r + rr * step, r, "red" if g else color, "red" if g else color, dash=g)
        return self

    def shop(self, cx, base, w=64, h=46, color="green", label=None):
        """一间小店（= 一家公司）：屋顶 + 墙 + 门。base 是地面 y。"""
        x = cx - w / 2
        self.rect(x, base - h, w, h, "ink", color, r=3)
        self.poly([(x - 7, base - h), (cx, base - h - 20), (x + w + 7, base - h)], "ink", "card")
        self.rect(cx - 7, base - 20, 14, 20, "ink", "card", r=2)
        if label:
            self.text(cx, base - h + 16, label, size=12, bold=True)
        return self

    def doc(self, x, y, w=44, h=54, color="card", rows=3, stroke="ink"):
        """一张纸（合同 / 公告 / 财报）。"""
        self.rect(x, y, w, h, stroke, color, r=3)
        for i in range(rows):
            self.line(x + 8, y + 14 + i * 11, x + w - 8, y + 14 + i * 11, "ink2", cls="thin")
        return self

    def bubble(self, x, y, w, h, tail="left", stroke="ink", fill="card"):
        """对话气泡；尾巴在左下或右下。文字自己用 text() 写进去。"""
        self.rect(x, y, w, h, stroke, fill, r=12)
        tx = x + 22 if tail == "left" else x + w - 22
        self.path("M%s %sL%s %sL%s %s" % (_n(tx - 7), _n(y + h), _n(tx + (-9 if tail == "left" else 9)), _n(y + h + 12),
                                          _n(tx + 7), _n(y + h)), stroke, fill)
        return self

    def bar(self, x, y, w, h, color="blue", dash=False):
        return self.rect(x, y, w, h, color, color, dash=dash, r=3)

    # ---- 输出与检查
    def svg(self, extra_class=""):
        return ('<svg class="chk%s" viewBox="0 0 %s %s" role="img" aria-label="%s" data-name="%s">'
                '<g filter="url(#wob)">%s</g><g>%s</g></svg>') % (
            " " + extra_class if extra_class else "", _n(self.w), _n(self.h), _esc(self.name), _esc(self.name),
            "".join(self._sh), "".join(self._tx))

    def lint(self, capmax=15):
        out = []
        for b in self.boxes:
            if b.x0 < 0 or b.y0 < 0 or b.x1 > self.w or b.y1 > self.h:
                out.append("[越界] %s :: %s" % (self.name, b.s))
            if self.panels and not any(b.x0 >= px + 3 and b.y0 >= py + 3 and b.x1 <= px + pw - 3 and b.y1 <= py + ph - 3
                                       for px, py, pw, ph in self.panels):
                out.append("[压格线] %s :: %s" % (self.name, b.s))
            if b.cap:
                n = len(re.sub(r"\s", "", b.s))
                if n > capmax:
                    out.append("[说明超长 %d>%d] %s :: %s" % (n, capmax, self.name, b.s))
        for i, a in enumerate(self.boxes):
            for b in self.boxes[i + 1:]:
                if a.x0 + 1 < b.x1 and b.x0 + 1 < a.x1 and a.y0 + 1 < b.y1 and b.y0 + 1 < a.y1:
                    out.append("[文字重叠] %s :: “%s” × “%s”" % (self.name, a.s, b.s))
        return out


class Comic(Canvas):
    """两格漫画，统一画布 560×232。左格 = 烦恼，右格 = 办法。

    左格 x 8–272（中心 LX=140），右格 x 288–552（中心 RX=420）；
    你的绘图区是 y 44–188；格子说明由构造函数写在 y≈207，每条 ≤ 15 字（英文 ≤ 32 字符）。
    """
    LX, RX, TOP, BOTTOM = 140, 420, 44, 188

    def __init__(self, left_cap, right_cap, name="comic", heads=None):
        super().__init__(560, 232, name)
        lab = _L()
        heads = heads or (lab["pain"], lab["fix"])
        for x, head, cap, col in ((8, heads[0], left_cap, "orange"), (288, heads[1], right_cap, "green")):
            self._sh.append('<rect x="%d" y="8" width="264" height="216" rx="10" class="sh k-ink f-card panel"/>' % x)
            self.panels.append((x, 8, 264, 216))
            self.line(x + 12, 36, x + 12 + text_w(head, 15, True) + 6, 36, col, cls="bold")
            self.text(x + 15, 30, head, size=15, anchor="start", bold=True)
            self.line(x + 14, 192, x + 250, 192, "ink2", cls="thin dot")
            self.text(x + 132, 211, cap, size=14.5, cap=True)
        self.path("M275 108L283 116L275 124", "ink", cls="bold")


# ------------------------------------------------------------------ 现成图表
def snake(nodes, per_row=4, name="concept-chain"):
    """蛇形概念依赖链。nodes = [(概念名, 它带来的新问题), ...]，每行 per_row 个。"""
    lab = _L()
    bw, bh, px, py = 148, 44, 176, 104
    rows = math.ceil(len(nodes) / per_row)
    c = Canvas(760, 14 + rows * py - 26, name)
    x0 = (760 - (per_row - 1) * px - bw) / 2
    pos = []
    for i, (nm, _) in enumerate(nodes):
        r, k = divmod(i, per_row)
        pos.append((x0 + (k if r % 2 == 0 else per_row - 1 - k) * px, 12 + r * py, r))
    for i, (nm, br) in enumerate(nodes):
        x, y, r = pos[i]
        c.rect(x, y, bw, bh, "ink", "card")
        c.circle(x + 17, y + bh / 2, 10.5, "ink", "hl")
        c.text(x + 17, y + bh / 2 + 4.5, i + 1, size=12.5, bold=True)
        c.text(x + bw / 2 + 12, y + bh / 2 + 5.5, nm, size=_fit(nm, 15.5, bw - 44, True), bold=True)
        if br:
            s = lab["brings"] + br
            c.text(x + bw / 2, y + bh + 20, s, size=_fit(s, 12.5, px - 6), color="ink2")
        if i + 1 < len(nodes):
            nx, ny, nr = pos[i + 1]
            my = y + bh / 2
            if nr == r:
                if nx > x:
                    c.arrow(x + bw + 4, my, nx - 5, my, "orange")
                else:
                    c.arrow(x - 4, my, nx + bw + 5, my, "orange")
            else:
                side = 1 if r % 2 == 0 else -1
                ex = x + bw if side == 1 else x
                c.path("M%s %sC%s %s %s %s %s %s" % (_n(ex + 4 * side), _n(my), _n(ex + 36 * side), _n(my),
                                                   _n(ex + 36 * side), _n(my + py), _n(ex + 7 * side), _n(my + py)), "orange")
                c.path(Canvas._head(ex + 6 * side, my + py, 0 if side == -1 else math.pi, 9), "orange")
    return c


def metro(stations, name="route"):
    """地铁线路图：stations 是站名列表（3–4 站）。"""
    n = len(stations)
    c = Canvas(760, 96, name)
    xs = [380] if n == 1 else [96 + i * (568 / (n - 1)) for i in range(n)]
    c.line(xs[0] - 50, 38, xs[-1] + 50, 38, "green", cls="bold")
    c.path(Canvas._head(xs[-1] + 52, 38, 0, 11), "green", cls="bold")
    for i, (x, s) in enumerate(zip(xs, stations)):
        c.circle(x, 38, 14, "ink", "card")
        c.text(x, 43, i + 1, size=14, bold=True)
        c.text(x, 80, s, size=_fit(s, 15, (568 / max(n - 1, 1)) - 14, True), bold=True)
    return c


def paths_chart(history, scenarios, unit="$", h=340, name="paths", decimals=2):
    """走势概率图：左边历史价格折线，右边 2–3 条分叉路径，终点是价格区间色带（写 名称 + 概率）。

    history   = [(横轴标签, 价格), ...]   最后一个点就是"今天"
    scenarios = [dict(name="顺利整合", prob=35, lo=42.5, hi=46.75, color="green"), ...]
    概率加起来应为 100；图上会自动标注"主观估计，不是预测"。
    """
    lab = _L()
    if abs(sum(s["prob"] for s in scenarios) - 100) > 0.01:
        raise ValueError("scenarios 的概率之和必须是 100，现在是 %s" % sum(s["prob"] for s in scenarios))
    c = Canvas(760, h, name)
    L, T, B = 58, 44, h - 38
    xh0, xh1, xb0, xb1 = L + 16, 430, 540, 744
    vals = [p for _, p in history] + [s["lo"] for s in scenarios] + [s["hi"] for s in scenarios]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * .07
    lo, hi = lo - pad, hi + pad
    Y = lambda v: B - (v - lo) / (hi - lo) * (B - T)
    step = _nice((hi - lo) / 5)
    v = math.ceil(lo / step) * step
    while v <= hi:
        c.line(L, Y(v), xb1, Y(v), "ink2", cls="thin dot")
        c.text(L - 8, Y(v) + 4, "%s%s" % (unit, _n(v)), size=12, anchor="end", color="ink2")
        v += step
    c.line(L, T - 12, L, B).line(L, B, xb1 + 6, B)
    n = len(history)
    pts = [(xh0 + i * (xh1 - xh0) / max(n - 1, 1), Y(p)) for i, (_, p) in enumerate(history)]
    c.poly(pts, "blue", close=False, cls="bold")
    for (x, y), (lb, _) in zip(pts, history):
        c.circle(x, y, 3.2, "blue", "blue!")
        if lb:
            c.text(x, B + 18, lb, size=12, color="ink2")
    tx, ty = pts[-1]
    c.line(tx, T - 4, tx, B, "ink2", dash=True, cls="thin")
    c.text(tx, T - 12, "%s %s%.*f" % (lab["today"], unit, decimals, history[-1][1]), size=13.5, bold=True)
    c.text(xb1, T - 12, lab["prob_note"], size=12.5, anchor="end", color="ink2")
    for s in sorted(scenarios, key=lambda s: -s["hi"]):
        y1, y2 = Y(s["hi"]), Y(s["lo"])
        if y2 - y1 < 22:
            raise ValueError("色带“%s”只有 %.0fpx 高，写不下字：把 h 调大，或把区间拉开" % (s["name"], y2 - y1))
        col = s.get("color", "blue")
        c.rect(xb0, y1, xb1 - xb0, y2 - y1, col, col, dash=(col == "red"), r=6)
        t = "%s %s%%" % (s["name"], _n(s["prob"]))
        c.text((xb0 + xb1) / 2, (y1 + y2) / 2 + 5, t, size=_fit(t, 14.5, xb1 - xb0 - 14, True), bold=True)
        c.arrow(tx + 6, ty, xb0 - 6, (y1 + y2) / 2, col, dash=True)
    return c


def ruler_chart(points, xr, yr, iso=(), xlabel="每股盈利 EPS", ylabel="倍数 P/E", gauge=None,
                unit="$", name="ruler", h=360):
    """"尺子"：两个指标一张图，等值虚线（x × y = 常数，股票里就是等股价线），右侧可加一根量杯。

    points = [dict(name="公告前", x=2.0, y=20, color="blue", dx=10, dy=-10, anchor="start"), ...]
    iso    = (30, 36, 42, 48)  每条虚线上 x×y 相同
    gauge  = dict(label="确定性", level=0.45, was=0.8, hi="高", lo="低")  was = 之前的水位（画红色虚线）
    """
    c = Canvas(760, h, name)
    L, T, R, B = 70, 34, (556 if gauge else 716), h - 52
    X = lambda v: L + (v - xr[0]) / (xr[1] - xr[0]) * (R - L)
    Y = lambda v: B - (v - yr[0]) / (yr[1] - yr[0]) * (B - T)
    c.arrow(L, B, L, T - 14).arrow(L, B, R + 16, B)
    c.text(L - 4, T - 20, ylabel, size=13.5, anchor="start", bold=True)
    c.text((L + R) / 2, B + 40, xlabel, size=13.5, bold=True)
    for rng, horiz in ((xr, True), (yr, False)):
        step = _nice((rng[1] - rng[0]) / 5)
        v = math.ceil(rng[0] / step - 1e-9) * step
        while v <= rng[1] + 1e-9:
            if horiz:
                c.line(X(v), B, X(v), B + 5, cls="thin")
                c.text(X(v), B + 20, _n(v), size=12, color="ink2")
            elif v > rng[0]:
                c.line(L - 5, Y(v), L, Y(v), cls="thin")
                c.text(L - 9, Y(v) + 4, _n(v), size=12, anchor="end", color="ink2")
            v += step
    for P in iso:
        pts = []
        for i in range(61):
            x = xr[0] + (xr[1] - xr[0]) * i / 60
            y = P / x if x else float("inf")
            if yr[0] <= y <= yr[1]:
                pts.append((X(x), Y(y)))
        if len(pts) > 1:
            c.poly(pts, "ink2", dash=True, close=False, cls="thin")
            ex, ey = pts[-1]
            c.text(ex - 4, ey - 6, "%s%s" % (unit, _n(P)), size=12, anchor="end", color="ink2")
    for p in points:
        col = p.get("color", "blue")
        c.circle(X(p["x"]), Y(p["y"]), 6.5, col, col + "!")
        c.text(X(p["x"]) + p.get("dx", 10), Y(p["y"]) + p.get("dy", -9), p["name"], size=13, bold=True,
               anchor=p.get("anchor", "start"), color=col)
    if gauge:
        gx, gw, gt, gb = 628, 64, T + 26, B
        lvl = gb - gauge["level"] * (gb - gt - 8)
        c.rect(gx + 3, lvl, gw - 6, gb - lvl - 3, None, "blue", r=3)
        c.path("M%s %sL%s %sQ%s %s %s %sL%s %sQ%s %s %s %sL%s %s" % (
            _n(gx), _n(gt), _n(gx), _n(gb - 8), _n(gx), _n(gb), _n(gx + 8), _n(gb), _n(gx + gw - 8), _n(gb),
            _n(gx + gw), _n(gb), _n(gx + gw), _n(gb - 8), _n(gx + gw), _n(gt)), "ink", cls="bold")
        c.line(gx + 3, lvl, gx + gw - 3, lvl, "blue")
        if "was" in gauge:
            wy = gb - gauge["was"] * (gb - gt - 8)
            c.line(gx - 6, wy, gx + gw + 6, wy, "red", dash=True)
        for i in range(1, 5):
            ty = gb - i * (gb - gt - 8) / 4
            c.line(gx + gw - 12, ty, gx + gw, ty, cls="thin")
        c.text(gx + gw / 2, B + 40, gauge["label"], size=13.5, bold=True)
        if gauge.get("hi"):
            c.text(gx + gw + 10, gt + 12, gauge["hi"], size=12, anchor="start", color="ink2")
        if gauge.get("lo"):
            c.text(gx + gw + 10, gb - 2, gauge["lo"], size=12, anchor="start", color="ink2")
    return c


def waterfall(steps, unit="%", name="waterfall", h=280, total_label=None, total_color="blue", decimals=1):
    """瀑布图：把一个涨跌幅拆成几步。steps = [(标签, 变化量, 颜色), ...]，最后自动加一根"合计"。"""
    lab = _L()
    c = Canvas(760, h, name)
    L, R, T, B = 70, 730, 30, h - 46
    cum = [0.0]
    for _, d, _c in steps:
        cum.append(cum[-1] + d)
    lo, hi = min(cum), max(cum)
    span = (hi - lo) or 1.0
    pad = span * .22
    Y = lambda v: T + (hi + pad - v) / (span + 2 * pad) * (B - T)
    n = len(steps) + 1
    cw = (R - L) / n
    bw = cw * .46
    c.line(L, Y(0), R, Y(0))
    c.text(L - 8, Y(0) + 4, "0", size=12, anchor="end", color="ink2")
    fmt = lambda d: "%+.*f%s" % (decimals, d, unit)
    cols = list(steps) + [(total_label or lab["total"], cum[-1], total_color)]
    for i, (lb, d, col) in enumerate(cols):
        last = i == len(steps)
        a, b = (0.0, cum[-1]) if last else (cum[i], cum[i + 1])
        x = L + i * cw + (cw - bw) / 2
        y1, y2 = sorted((Y(a), Y(b)))
        c.rect(x, y1, bw, max(y2 - y1, 2), col, col, dash=(col == "red"), r=4)
        ty, band = ((y2 + 17), (y2 + 3, y2 + 20)) if d < 0 else ((y1 - 7), (y1 - 21, y1 - 4))
        if not last and band[0] <= Y(0) <= band[1]:   # 数字会压在 0 轴上：柱子够高就放进柱内，否则放到另一端
            if y2 - y1 >= 26:
                ty = (y2 - 7) if d < 0 else (y1 + 18)
            else:
                ty = (y1 - 7) if d < 0 else (y2 + 17)
        c.text(x + bw / 2, ty, fmt(d), size=14, bold=True, color=col)
        if text_w(lb, 12) > cw - 8 and " " in lb:     # 柱子多、标签长时拆成两行，避免相邻标签挤在一起
            l1, l2 = lb.split(" ", 1)
            c.text(x + bw / 2, B + 18, l1, size=_fit(l1, 12.5, cw - 8))
            c.text(x + bw / 2, B + 35, l2, size=_fit(l2, 12.5, cw - 8))
        else:
            c.text(x + bw / 2, B + 24, lb, size=_fit(lb, 13.5, cw - 10))
        if not last:
            c.line(x + bw, Y(b), x + cw, Y(b), "ink2", dash=True, cls="thin")
    return c


def timeline(events, name="timeline"):
    """关键时间节点：一条时间轴，标签上下交替。

    events = [dict(date="12/15", name="股东大会投票", sure=True, color="orange", now=False), ...]
    sure=False = 日期未确认 → 画虚线圈，date 自己写成"预计 1 月下旬"（不要把没公告的日期写死）。
    now=True   = "今天"这个点（实心）。按时间先后给，最多 6–7 个。
    """
    n = len(events)
    c = Canvas(760, 196, name)
    y = 98
    xs = [380] if n == 1 else [78 + i * (604 / (n - 1)) for i in range(n)]
    c.line(30, y, 728, y, "ink", cls="bold")
    c.path(Canvas._head(730, y, 0, 11), "ink", cls="bold")
    pitch = 2 * 604 / max(n - 1, 1)
    for i, (x, e) in enumerate(zip(xs, events)):
        up = i % 2 == 0
        sure, col = e.get("sure", True), e.get("color", "orange")
        if e.get("now"):
            c.circle(x, y, 9, "ink", "ink!")
        else:
            c.circle(x, y, 9, col, (col + "!") if sure else "card", dash=not sure)
        c.line(x, y - 12 if up else y + 12, x, y - 28 if up else y + 28, "ink2", cls="thin")
        maxw = min(pitch - 12, 2 * (x - 6), 2 * (754 - x))
        d, nm = str(e["date"]), str(e["name"])
        c.text(x, y - 56 if up else y + 46, d, size=_fit(d, 13.5, maxw, True), bold=True, color="ink" if sure else "ink2")
        c.text(x, y - 37 if up else y + 65, nm, size=_fit(nm, 12.5, maxw))
    return c


def roadmap(stages, name="roadmap"):
    """规划路线：一级级往上的台阶。stages = [(时间, 标题, [要点, ...]), ...],2–4 级，每级 ≤3 个要点。

    第一级 = 正在做（绿）；后面 = 还没发生（橙，越远越虚）。技术路线、产品路线、远期规划都能用。
    """
    n = len(stages)
    rise, gap = 26, 12
    w = (708 - (n - 1) * gap) / n
    H = 24 + (n - 1) * rise + 138   # 最低一级也要放得下 3 个要点（原 122 时第 3 行贴框底）
    c = Canvas(760, H, name)
    for i, (when, title, items) in enumerate(stages):
        x, top = 26 + i * (w + gap), 14 + (n - 1 - i) * rise
        col = "green" if i == 0 else "orange"
        c.rect(x, top, w, H - 12 - top, col, col, dash=(i >= 2), r=10)
        c.text(x + 14, top + 24, when, size=_fit(when, 13, w - 26), anchor="start", color="ink2")
        c.text(x + 14, top + 48, title, size=_fit(title, 16.5, w - 26, True), anchor="start", bold=True)
        for k, it in enumerate(items[:3]):
            t = "· " + it
            c.text(x + 14, top + 73 + k * 22, t, size=_fit(t, 13.5, w - 26), anchor="start")
        if i + 1 < n:
            c.curve(x + w - 26, top - 2, x + w + gap + 22, top - rise - 2, bend=0.35, stroke="ink2", cls="thin")
    return c


def risk_matrix(items, xlabel=None, ylabel=None, name="risks", h=340):
    """隐藏危机：可能性 × 杀伤力 四象限。右上角 = 先盯这里。

    items = [dict(name="审批被否", p=0.3, impact=0.9, color="red", dx=12, dy=5, anchor="start"), ...]
    p / impact 取 0–1，都是主观估计（图上会自动注明）；正文里要配一张"预警信号"表。
    """
    lab = _L()
    c = Canvas(760, h, name)
    L, T, R, B = 70, 36, 716, h - 54
    mx, my = (L + R) / 2, (T + B) / 2
    c.rect(mx, T, R - mx, my - T, None, "red", r=0)
    c.arrow(L, B, L, T - 16).arrow(L, B, R + 18, B)
    c.line(mx, T, mx, B, "ink2", dash=True, cls="thin").line(L, my, R, my, "ink2", dash=True, cls="thin")
    c.text(L - 4, T - 22, ylabel or lab["impact"], size=13.5, anchor="start", bold=True)
    c.text(mx, B + 40, xlabel or lab["likely"], size=13.5, bold=True)
    c.text(L + 6, B + 20, lab["low"], size=12, anchor="start", color="ink2")
    c.text(R - 6, B + 20, lab["high"], size=12, anchor="end", color="ink2")
    c.text(R - 10, T + 20, lab["focus"], size=13, anchor="end", bold=True, color="red")
    c.text(R, B + 40, lab["subjective"], size=12, anchor="end", color="ink2")
    for it in items:
        col = it.get("color", "red")
        x, y = L + it["p"] * (R - L), B - it["impact"] * (B - T)
        c.circle(x, y, 7, col, col + "!")
        c.text(x + it.get("dx", 12), y + it.get("dy", 5), it["name"], size=13, bold=True, anchor=it.get("anchor", "start"))
    return c


# ------------------------------------------------------------------ 页面
class Stop:
    """学习路线的一站。url 必须先用抓取工具打开核实过内容，再写 verified=True；核实不了就不给 url。"""

    def __init__(self, name, why, time, url=None, link_text=None, verified=False):
        self.name, self.why, self.time, self.url, self.link_text, self.verified = name, why, time, url, link_text, verified


_ICON = {
    "ok": '<svg viewBox="0 0 26 26" aria-label="ok"><g filter="url(#wob)"><rect width="26" height="26" fill="none"/><path d="M4 14L10 21L22 5" class="sh bold k-green"/></g></svg>',
    "mid": '<svg viewBox="0 0 26 26" aria-label="neutral"><g filter="url(#wob)"><rect width="26" height="26" fill="none"/><path d="M5 13L21 13" class="sh bold k-orange"/></g></svg>',
    "bad": '<svg viewBox="0 0 26 26" aria-label="bad"><g filter="url(#wob)"><rect width="26" height="26" fill="none"/><path d="M5 5L21 21M21 5L5 21" class="sh bold k-red"/></g></svg>',
}
_NO_COST = re.compile(r"(没有|无|零|几乎没|基本没)\s*(什么)?\s*代价|^\s*(无|没有|none|n/?a|no cost)\s*[。.]?\s*$", re.I)


class Page:
    """整页。kind="stock"（默认）是一份完整的个股图解报告，缺下面任何一节都会报警：

      mainline 主线 → checkup 体检单 → section(role="moat") 核心竞争力 → chain + card × N 概念
      → section(role="roadmap") 技术/产品规划路线 → section(role="vision") 远期规划
      → section(role="risks") 隐藏危机 → section(role="timeline") 关键时间节点
      → section(role="paths") 股价推演 → section(role="ruler") 尺子 → section(role="eli5") 零基础版（按需）
      → route 学习路线 → sources 来源
    这是"至少要有"，不是"只能有"：材料里有别的重点（估值、同行对比、管理层、资本开支…）就再加 section。
    kind="general" 用于非股票的学习资料，只要求 主线 / 依赖链 / 学习路线。
    """
    STOCK_ROLES = ("checkup", "moat", "roadmap", "vision", "risks", "timeline", "paths", "ruler")

    def __init__(self, title, subtitle="", kind="stock", notice=None, kicker=None, credit=True):
        self.title, self.subtitle, self.kind, self.notice, self.kicker, self.credit = title, subtitle, kind, notice, kicker, credit
        self._blocks, self._canvases, self._issues, self._warn = [], [], [], []
        self._cards, self._chain_n, self._roles, self._sources, self._no = [], 0, set(), [], 0
        self.lab = _L()

    # ---- 内部
    def _h2(self, title, small=None):
        self._no += 1
        return '<h2><span class="no">%d</span>%s%s</h2>' % (self._no, _inline(title), " <small>%s</small>" % _inline(small) if small else "")

    def _fig(self, canvas, frame=True):
        self._canvases.append(canvas)
        return '<figure%s>%s</figure>' % (' class="frame"' if frame else "", canvas.svg())

    def _prose(self, where, text, cls="prose"):
        if not text:
            return ""
        n = _sentences(text)
        if n > 4:
            self._issues.append("[正文超 4 句：%d 句] %s" % (n, where))
        return '<p class="%s">%s</p>' % (cls, _inline(text))

    def _flush_cards(self):
        if not self._cards:
            return
        head = self._h2(self.lab["cards"])
        prog = '<p class="progress">%s</p>' % self.lab["progress"].format(m=len(self._cards))
        self._blocks.append('<section class="sec cards" id="cards">%s%s%s</section>' % (head, prog, "".join(self._cards)))
        self._n_cards = len(self._cards)
        self._cards = []

    @staticmethod
    def table(headers, rows):
        """返回表格 HTML；单元格允许内联 HTML。"""
        th = "".join("<th>%s</th>" % _inline(h) for h in headers)
        tr = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _inline(c) for c in r) for r in rows)
        return '<div class="tblwrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, tr)

    # ---- 页面各部分
    def mainline(self, sentence, canvas, kind=None, title=None, note=None):
        """主线：一句话 + 一张图。kind 写"主循环" / "流水线" / "核心矛盾"之一。"""
        self._flush_cards()
        self._roles.add("mainline")
        if _sentences(sentence) > 1:
            self._issues.append("[主线必须是一句话] %s" % _plain(sentence))
        self._blocks.append('<section class="sec" id="mainline">%s<p class="lead">%s</p>%s%s</section>' % (
            self._h2(title or self.lab["mainline"], kind), _inline(sentence), self._fig(canvas),
            '<p class="note">%s</p>' % _inline(note) if note else ""))
        return self

    def checkup(self, items, title=None, intro=None, small=None):
        """体检单：items = [("ok" | "mid" | "bad", "带具体数字和口径的一行"), ...]"""
        self._flush_cards()
        self._roles.add("checkup")
        for kind, text in items:
            if kind not in _ICON:
                raise ValueError("体检单图标只能是 ok / mid / bad")
            if not re.search(r"\d", _plain(text)):
                self._warn.append("[体检单这一行没有具体数字] %s" % _plain(text))
        lis = "".join("<li>%s<span>%s</span></li>" % (_ICON[k], _inline(t)) for k, t in items)
        self._blocks.append('<section class="sec" id="checkup">%s%s<ul class="checkup frame">%s</ul></section>' % (
            self._h2(title or self.lab["checkup"], small), self._prose("体检单", intro), lis))
        return self

    def chain(self, nodes, intro=None, title=None, per_row=4):
        """概念依赖链：nodes = [(概念名, 它带来的新问题), ...]，顺序 = 依赖顺序。"""
        self._flush_cards()
        self._roles.add("chain")
        self._chain_n = len(nodes)
        for nm, br in nodes[:-1]:
            if not br:
                self._issues.append("[依赖链断了] “%s”说不出它带来什么新问题 → 排错了，重排" % nm)
        self._blocks.append('<section class="sec" id="chain">%s%s%s</section>' % (
            self._h2(title or self.lab["chain"]), self._prose("依赖链", intro or self.lab["chain_note"]),
            self._fig(snake(nodes, per_row))))
        return self

    def card(self, name, en, definition, comic, solves, cost, stamp="next"):
        """概念卡片。stamp: "next" 下一站 / "redo" 补一下 / "done" 已学（读者可以自己点着改）。"""
        i = len(self._cards) + 1
        if not en:
            self._warn.append("[卡片缺英文原词] %s" % name)
        if not cost or _NO_COST.search(_plain(cost)):
            self._issues.append("[代价不能留空或写“没有代价”] %s" % name)
        for label, t in (("定义", definition), ("解决了什么", solves), ("代价是什么", cost)):
            if _sentences(t) > 2:
                self._warn.append("[卡片“%s”的%s偏长，尽量一句话] " % (name, label))
        comic.name = "comic-%d %s" % (i, name)
        self._canvases.append(comic)
        s = {"next": 0, "redo": 1, "done": 2}[stamp]
        self._cards.append(
            '<article class="card" id="c%d"><button type="button" class="stamp" data-s="%d">%s</button>'
            '<h3><span class="idx">%d</span>%s<span class="en">%s</span></h3><p class="def">%s</p>'
            '<figure>%s</figure><p class="kv"><b>%s</b>%s</p><p class="kv"><b>%s</b>%s</p></article>' % (
                i, s, self.lab["stamps"][s], i, _inline(name), _esc(en or ""), _inline(definition), comic.svg("comic"),
                self.lab["solves"], _inline(solves), self.lab["cost"], _inline(cost)))
        return self

    def section(self, title, prose=None, canvas=None, table=None, steps=None, tiles=None, after=None, note=None,
                small=None, role=None, id=None):
        """通用小节：结论先行的正文（≤4 句）+ 图 + 步骤 + 表 + 小字注。

        role: 这一节在报告里的身份，股票类靠它检查有没有漏节 ——
              "moat" 核心竞争力 / "roadmap" 技术规划路线 / "vision" 远期规划 / "risks" 隐藏危机 /
              "timeline" 关键时间节点 / "paths" 股价推演 / "ruler" 尺子 / "eli5" 零基础版。
        tiles: 一排小卡片 [(标题, 正文, 小字), ...]，适合"每条竞争力 + 证据 + 弱点"。
        table: (表头, 行) 或 Page.table() 的结果；steps: 带算式的编号步骤列表；
        after: 表格后面再跟一段（同样 ≤4 句，比如"财报后的机会"）；note: 小字注。
        """
        self._flush_cards()
        if role:
            self._roles.add(role)
        parts = [self._h2(title, small), self._prose(title, prose)]
        if canvas is not None:
            parts.append(self._fig(canvas))
        if tiles:
            parts.append('<div class="stops">%s</div>' % "".join(
                '<div class="stop"><h4>%s</h4><p>%s</p>%s</div>' % (
                    _inline(t[0]), _inline(t[1]), '<p class="t">%s</p>' % _inline(t[2]) if len(t) > 2 and t[2] else "")
                for t in tiles))
        if steps:
            parts.append('<ol class="steps frame">%s</ol>' % "".join("<li>%s</li>" % _inline(s) for s in steps))
        if table:
            parts.append(table if isinstance(table, str) else self.table(*table))
        if after:
            parts.append(self._prose(title + "(after)", after))
        if note:
            parts.append('<p class="note">%s</p>' % _inline(note))
        self._blocks.append('<section class="sec" id="%s">%s</section>' % (_esc(id or role or "s%d" % self._no), "".join(parts)))
        return self

    def route(self, stops, intro=None, title=None):
        """学习路线：3–4 个 Stop。带 url 的必须 verified=True(= 你真的打开核实过)。"""
        self._flush_cards()
        self._roles.add("route")
        cards = []
        for i, s in enumerate(stops):
            if s.url and not s.verified:
                self._issues.append("[链接未核实] %s → %s(先用抓取工具打开，内容对得上再写 verified=True)" % (s.name, s.url))
            link = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (_esc(s.url), _inline(s.link_text or s.url))
                    if s.url else "%s %s" % (_inline(s.link_text or s.name), self.lab["search"]))
            cards.append('<div class="stop"><h4>%d · %s</h4><p><b>%s</b>%s</p><p class="t"><b>%s</b>%s</p><p>%s</p></div>' % (
                i + 1, _inline(s.name), self.lab["why"], _inline(s.why), self.lab["time"], _inline(s.time), link))
        self._blocks.append('<section class="sec" id="route">%s%s%s<div class="stops">%s</div></section>' % (
            self._h2(title or self.lab["route"]), self._prose("学习路线", intro),
            self._fig(metro([s.name for s in stops])), "".join(cards)))
        return self

    def sources(self, items):
        """页脚来源：[(标题, url 或 None), ...]。一手来源优先。"""
        self._sources = list(items)
        return self

    # ---- 输出
    def lint(self):
        self._flush_cards()
        errs, warns = list(self._issues), list(self._warn)
        for c in self._canvases:
            errs += c.lint(self.lab["capmax"])
        n = getattr(self, "_n_cards", 0)
        if self._chain_n and n and self._chain_n != n:
            errs.append("[依赖链 %d 个概念，卡片却有 %d 张] 两边必须一一对应" % (self._chain_n, n))
        if n and not 8 <= n <= 13:
            warns.append("[概念数 %d 不在 8–13] 太少讲不透，太多记不住（小主题可以忽略）" % n)
        need = ["mainline", "chain", "route"] + (list(self.STOCK_ROLES) if self.kind == "stock" else [])
        names = {"mainline": "主线", "chain": "概念依赖链", "route": "学习路线", "checkup": "体检单", "moat": "核心竞争力",
                 "roadmap": "技术规划路线", "vision": "远期规划", "risks": "隐藏危机", "timeline": "关键时间节点",
                 "paths": "股价推演", "ruler": "尺子"}
        for r in need:
            if r not in self._roles:
                warns.append("[缺小节] %s(role=\"%s\")" % (names[r], r))
        if self.kind == "stock" and not self._sources:
            warns.append("[股票类必须列出来源]")
        return errs, warns

    def html(self):
        self._flush_cards()
        lab = self.lab
        legend = "".join('<li><svg viewBox="0 0 26 14"><rect x="1.5" y="1.5" width="23" height="11" rx="3" class="sh k-%s f-%s%s"/></svg>%s</li>' % (
            c, c, " dash" if c == "red" else "", _esc(t)) for c, t in lab["legend"])
        hero = ('<header class="hero"><button type="button" class="theme-btn" id="themeBtn" aria-label="theme"></button>'
                '<p class="kicker">%s</p><h1>%s</h1>%s<ul class="legend">%s</ul>%s</header>') % (
            _inline(self.kicker or lab["kicker"]), _inline(self.title),
            '<p class="sub">%s</p>' % _inline(self.subtitle) if self.subtitle else "", legend,
            '<p class="notice">%s</p>' % _inline(self.notice) if self.notice else "")
        foot = ['<footer>']
        if self._sources:
            foot.append('<h2>%s</h2><ol>%s</ol>' % (lab["sources"], "".join(
                "<li>%s</li>" % ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (_esc(u), _inline(t)) if u else _inline(t))
                for t, u in self._sources)))
        if self.kind == "stock":
            foot.append('<p class="disc">%s</p>' % lab["disc"])
        if self.credit:
            foot.append('<p class="made"><a href="%s" target="_blank" rel="noopener">%s</a></p>' % (REPO_URL, lab["made"]))
        foot.append("</footer>")
        body = hero + "\n" + "\n".join(self._blocks) + "\n" + "".join(foot)
        tpl = (Path(__file__).resolve().parent.parent / "assets" / "template.html").read_text(encoding="utf-8")
        labels = json.dumps({k: lab[k] for k in ("stamps", "toDark", "toLight")}, ensure_ascii=False)
        for k, v in (("{{LANG}}", lab["html_lang"]), ("{{CAPMAX}}", str(lab["capmax"])), ("{{TITLE}}", _esc(_plain(self.title))),
                     ("{{PAGE_KEY}}", json.dumps(_plain(self.title), ensure_ascii=False)), ("{{LABELS}}", labels), ("{{BODY}}", body)):
            tpl = tpl.replace(k, v)
        return tpl

    def save(self, path, strict=True):
        """写出单文件 HTML 并打印检查报告。strict=True 时有错误就以退出码 1 结束（文件照样写出，方便看）。"""
        out = self.html()
        errs, warns = self.lint()
        Path(path).write_text(out, encoding="utf-8")
        print("wrote %s  (%.0f KB, %d svg)" % (path, len(out.encode("utf-8")) / 1024, len(self._canvases)))
        for w in warns:
            print("  warn  " + w)
        for e in errs:
            print("  ERROR " + e)
        print("[precheck] %s — %d error(s), %d warning(s). 下一步：python3 verify.py %s" % (
            "FAIL" if errs else "PASS", len(errs), len(warns), path))
        if errs and strict:
            sys.exit(1)
        return errs, warns


if __name__ == "__main__":
    print(__doc__)
