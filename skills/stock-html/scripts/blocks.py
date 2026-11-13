"""blocks.py — 建立在 sketch.py 之上的“半成品积木”：一行代码画出常用的主线图、护城河、远期对账图和三种两格漫画。

一次做多份报告（比如一个 ETF 的前十大成分股）时用它最省事；单份报告想画得更讲究，仍可直接用 Canvas / Comic 手画。

    import sys; sys.path.insert(0, "<本 skill 目录>/scripts")
    from blocks import *          # 同时导入了 sketch 里的全部工具
    m  = mainline_tug(...)        # 主线：左边生意（3 根柱）· 中间问题框 · 右边股价折线
    mo = moat([...3 道...], "TICK")
    vi = vision([(值, 标签1, 标签2, 颜色, 虚线) × 3], gap_between=(1, 2), note="算法…")
    c1 = C_bars(...) / C_talk(...) / C_flow(...)      # 三种两格漫画版式
    sc = [scen("路径", 概率, 示意EPS, 低倍数, 高倍数, "green"), ...]; expect(sc); scen_table(sc, needs)

所有文字仍走 Canvas.text()，离线预检和 verify.py 的检查照样生效。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sketch import *  # noqa: E402,F403
from sketch import _fit  # noqa: E402

# ---------------------------------------------------------------- 主线：生意 vs 股价
def mainline_tug(left_title, bars, unit_note, center_q, center_sub, forces, right_title, prices, price_note,
                 foot="收入为公司公布值；股价为收盘价", left_color="green"):
    """左：3 根收入柱 (标签, 数值, 是否指引)；中：问题框 + 3 条力量；右：近期股价折线 [(标签, 价格), ...]。"""
    m = Canvas(760, 272, "mainline")
    m.text(150, 30, left_title, size=16, bold=True, color=left_color)
    m.text(620, 30, right_title, size=16, bold=True, color="blue")
    vmax = max(v for _, v, _g in bars)
    k = 118 / vmax
    for i, (lab, val, guide) in enumerate(bars):
        x = 50 + i * 72
        m.bar(x, 186 - val * k, 48, val * k, "orange" if guide else "green", dash=guide)
        m.text(x + 24, 180 - val * k, "%g" % val, size=12.5, bold=True)
        m.text(x + 24, 206, lab, size=_fit(lab, 12.5, 68), color="ink2")
    m.text(150, 232, unit_note, size=13, color="ink2")
    m.rect(296, 86, 168, 64, "ink", "hl").text(380, 113, center_q, size=_fit(center_q, 15, 156, True), bold=True)
    m.text(380, 137, center_sub, size=_fit(center_sub, 12.5, 156), color="ink2")
    m.arrow(232, 120, 290, 120, "green").arrow(470, 120, 520, 120, "blue", dash=True)
    for i, (txt, col) in enumerate(forces):
        m.text(380, 186 + i * 22, txt, size=_fit(txt, 13, 220, True), bold=True, color=col)
    ps = [p for _, p in prices]
    lo, hi = min(ps), max(ps)
    span = (hi - lo) or 1
    pts = [(546 + i * (160 / (len(prices) - 1)), 150 - (p - lo) / span * 80) for i, (_, p) in enumerate(prices)]
    m.poly(pts, "blue", close=False, cls="bold")
    for (x, y), (lab, p) in zip(pts, prices):
        m.circle(x, y, 3, "blue", "blue!")
    up0 = pts[1][1] < pts[0][1]          # 折线往上走时，把起点标签放到点下方，免得压线
    m.text(pts[0][0], pts[0][1] + (22 if up0 else -10), "$%g" % prices[0][1], size=12.5, bold=True)
    m.text(pts[-1][0], pts[-1][1] - 10, "$%g" % prices[-1][1], size=12.5, bold=True, color="blue")
    m.text(626, 180, "%s → %s" % (prices[0][0], prices[-1][0]), size=12.5, color="ink2")
    m.text(626, 204, price_note, size=15, bold=True, color="red" if price_note.startswith("−") else "green")
    m.text(744, 262, foot, size=12, anchor="end", color="ink2")
    return m


# ---------------------------------------------------------------- 护城河
def moat(labels, center):
    """labels: 由内到外 3 道（第 3 道画虚线 = 最浅）。"""
    c = Canvas(760, 214, "moat")
    for r, lab, dash in zip((130, 190, 250), labels, (False, False, True)):
        c.path("M%d 196A%d %d 0 0 1 %d 196" % (380 - r, r, r * 0.6, 380 + r), "blue", dash=dash, cls="bold")
        c.text(380, 196 - r * 0.6 - 8, lab, size=_fit(lab, 13.5, 2 * r - 40, True), bold=True)
    c.shop(380, 194, w=62, h=40, color="green", label=center)
    return c


# ---------------------------------------------------------------- 远期规划：3 根柱 + 差额
def vision(bars, gap_between=None, unit="$", suffix=" 亿", note=None, h=270, fmt="%.0f"):
    """bars = [(值, 标签1, 标签2, 颜色, 虚线), ...] 3 根；gap_between=(i, j) 在第 i 根上方画出到第 j 根高度的红色差额。"""
    h = h + (20 if note else 0)
    v = Canvas(760, h, "vision")
    base = h - 56 - (20 if note else 0)
    vmax = max(b[0] for b in bars)
    k = (base - 50) / vmax
    v.line(60, base, 700, base)
    tops = []
    for i, (val, l1, l2, col, dash) in enumerate(bars):
        x = 110 + i * 200
        v.bar(x, base - val * k, 120, val * k, col, dash=dash)
        tops.append((x, base - val * k))
        inside = gap_between and i == gap_between[0] and bars[gap_between[1]][0] > val
        v.text(x + 60, base - val * k + (26 if inside else -9), unit + (fmt % val) + suffix, size=14, bold=True)
        v.text(x + 60, base + 22, l1, size=_fit(l1, 13, 180)).text(x + 60, base + 41, l2, size=_fit(l2, 12, 180), color="ink2")
    if gap_between:
        i, j = gap_between
        gi, gj = bars[i][0], bars[j][0]
        if gj > gi:
            x, top_i = tops[i]
            top_j = base - gj * k
            v.rect(x, top_j, 120, top_i - top_j, "red", "red", dash=True, r=3)
            v.text(x + 60, top_j - 9, "还差 %s%s%s" % (unit, fmt % (gj - gi), suffix), size=13.5, bold=True, color="red")
    if note:
        v.text(744, h - 4, note, size=12, anchor="end", color="ink2")
    return v


# ---------------------------------------------------------------- 三种两格漫画
def C_bars(lc, rc, left, right, lnote=None, rnote=None, fmt="%g"):
    """左右各一组柱：[(标签, 数值, 颜色), ...]，同一比例尺。"""
    k = Comic(lc, rc)
    vmax = max(v for _, v, _c in left + right) or 1
    for side, group, note in ((28, left, lnote), (308, right, rnote)):
        n = len(group)
        w = min(56, (220 - (n - 1) * 14) / n)
        for i, (lab, val, col) in enumerate(group):
            x = side + 12 + i * (w + 14)
            hh = max(4, val / vmax * (92 if note else 118))
            k.bar(x, 168 - hh, w, hh, col, dash=(col == "red"))
            k.text(x + w / 2, 162 - hh, fmt % val, size=_fit(fmt % val, 12.5, w + 12), bold=True)
            k.text(x + w / 2, 184, lab, size=_fit(lab, 12, w + 12), color="ink2")
        if note:
            k.text(side + 112, 54, note, size=_fit(note, 13, 220, True), bold=True)
    return k


def C_talk(lc, rc, lwho, lsay, lobj, rwho, robj, rnote, lcol="blue", rcol="orange", lobj_col="card", robj_col="green"):
    """左：犯愁的角色 + 气泡 + 一个物件；右：开心的角色 + 物件 + 一行注。"""
    k = Comic(lc, rc)
    k.bubble(26, 50, 130, 32).text(91, 71, lsay, size=_fit(lsay, 12.5, 120))
    k.person(64, 100, lwho, lcol, "sad")
    k.rect(140, 100, 112, 54, "ink", lobj_col, r=6).text(196, 132, lobj, size=_fit(lobj, 13, 104, True), bold=True)
    k.person(336, 92, rwho, rcol, "happy")
    k.rect(392, 84, 144, 58, "ink", robj_col, r=6).text(464, 118, robj, size=_fit(robj, 13.5, 136, True), bold=True)
    k.text(420, 176, rnote, size=_fit(rnote, 12.5, 240), color="ink2")
    return k


def C_flow(lc, rc, lboxes, rboxes, lbad=True, lcols=None, rcols=None, lnote=None, rnote=None):
    """左右各一串方框（2–3 个）用箭头连起来；左边可在最后一个箭头上打叉。"""
    k = Comic(lc, rc)
    for side, boxes, cols, bad, note in ((20, lboxes, lcols, lbad, lnote), (300, rboxes, rcols, False, rnote)):
        n = len(boxes)
        bw = (240 - (n - 1) * 22) / n
        for i, lab in enumerate(boxes):
            x = side + i * (bw + 22)
            col = (cols or ["card"] * n)[i]
            k.rect(x, 92, bw, 50, "ink", col, r=6).text(x + bw / 2, 122, lab, size=_fit(lab, 13, bw - 8, True), bold=True)
            if i + 1 < n:
                k.arrow(x + bw + 3, 117, x + bw + 19, 117, "red" if (bad and i == n - 2) else "ink")
        if bad:
            k.cross(side + (n - 1) * (bw + 22) - 11, 96, 7)
        if note:
            k.text(side + 120, 172, note, size=_fit(note, 12.5, 240), color="ink2")
    return k


# ---------------------------------------------------------------- 推演：示意 EPS × 倍数
def scen(name, prob, eps, lo_x, hi_x, color):
    return dict(name=name, prob=prob, eps=eps, lo_x=lo_x, hi_x=hi_x, lo=eps * lo_x, hi=eps * hi_x, color=color)


def expect(sc):
    assert abs(sum(s["prob"] for s in sc) - 100) < 1e-9
    return sum(s["prob"] / 100 * (s["lo"] + s["hi"]) / 2 for s in sc)


def scen_table(sc, needs):
    return (["路径", "需要发生什么", "示意 EPS × 倍数", "价格区间", "概率"], [
        [s["name"], need, "$%.2f × %g–%g 倍" % (s["eps"], s["lo_x"], s["hi_x"]), "$%.0f – %.0f" % (s["lo"], s["hi"]), "%d%%" % s["prob"]]
        for s, need in zip(sc, needs)])



# ---------------------------------------------------------------- 重大事件：前后对比（人事、组织、股权结构）
def org_change(before, after, left_title="之前", right_title="之后", gone=None, note=None, name="org-change"):
    """左右两列方框对比一次结构变化，常用于 CEO / 董事会调整。

    before / after = [(角色, 说明, 颜色), ...]，每列 2–4 个；颜色用语义名（新来的用 "orange"）。
    gone = 左列里“离开”的那一项的序号：画红色虚线框 + 叉，表示作废 / 离任。
    """
    n = max(len(before), len(after))
    bh, gap = 52, 14
    h = 70 + n * (bh + gap) + (24 if note else 0)
    c = Canvas(760, h, name)
    c.text(190, 30, left_title, size=16, bold=True).text(570, 30, right_title, size=16, bold=True)
    for col_x, items, is_left in ((60, before, True), (440, after, False)):
        for i, (role, desc, color) in enumerate(items):
            y = 50 + i * (bh + gap)
            out = is_left and gone == i
            c.rect(col_x, y, 260, bh, "red" if out else "ink", "red" if out else color, dash=out, r=8)
            c.text(col_x + 14, y + 22, role, size=_fit(role, 14, 232, True), anchor="start", bold=True)
            c.text(col_x + 14, y + 42, desc, size=_fit(desc, 12.5, 232), anchor="start", color="ink2")
            if out:
                c.cross(col_x + 238, y + bh / 2, 9)
    mid_y = 50 + (n * (bh + gap) - gap) / 2
    c.arrow(334, mid_y, 426, mid_y, "orange", cls="bold")
    if note:
        c.text(744, h - 8, note, size=12, anchor="end", color="ink2")
    return c


def disclaimer(as_of, extra=""):
    """页面顶部提示条的标准写法：数据截止日 + 免责声明。"""
    return "数据截至 %s 收盘；盘后价格会变动。仅作学习用途，不构成投资建议。%s" % (as_of, (" " + extra) if extra else "")
