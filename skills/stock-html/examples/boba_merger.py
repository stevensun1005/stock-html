#!/usr/bin/env python3
"""完整示例：一份个股图解报告（虚构公司）。

    python3 boba_merger.py [输出路径.html]

这是 stock-html 的参考写法，照着它的顺序写你自己的 build 脚本：
  ① 先把所有数字放在最上面，用断言互相对账（算不平就不许画图）
  ② 排依赖链 → 画两格漫画 → 拼页面
  ③ page.save() 做离线预检，再跑 scripts/verify.py 做真实渲染检查

波波茶 BOBA、珍珠工厂 PEARL 都是虚构公司，数字只为演示页面结构。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from sketch import *  # noqa: E402,F403

# ============================================================ ① 数字：先算平，再画图
BOBA_SH, BOBA_P0, BOBA_NI = 6.0, 40.00, 12.0      # 亿股 / 公告前股价 / 年净利润（亿）
PEARL_SH, PEARL_P0, PEARL_NI = 4.0, 15.00, 3.0
RATIO, SYNERGY, FEE = 0.5, 2.0, 3.0               # 换股比例 / 协同（亿/年）/ 分手费（亿）

NEW_SH = PEARL_SH * RATIO                          # 新发 2 亿股
ALL_SH = BOBA_SH + NEW_SH                          # 8 亿股
EPS0 = BOBA_NI / BOBA_SH                           # 2.00
EPS_NO = (BOBA_NI + PEARL_NI) / ALL_SH             # 1.875
EPS_SYN = (BOBA_NI + PEARL_NI + SYNERGY) / ALL_SH  # 2.125
EPS_HALF = (BOBA_NI + PEARL_NI + SYNERGY / 2) / ALL_SH
DEAL = PEARL_SH * RATIO * BOBA_P0                  # 80 亿
PREMIUM = RATIO * BOBA_P0 / PEARL_P0 - 1           # 33.3%

P1 = BOBA_P0 * 0.95                                # 公告日 38.00
PEARL1 = P1 * RATIO * (1 - 0.05)                   # 18.05
P2 = P1 * 0.95                                     # 今天 36.10
PEARL_FLAT = P2 * RATIO * (1 - 0.05)               # 价差不变时 17.15
PEARL2 = P2 * RATIO * (1 - 0.08)                   # 16.61
D_BOBA = P2 / P1 - 1                               # -5.0%
D_PEARL = PEARL2 / PEARL1 - 1                      # -8.0%
D_SPREAD = D_PEARL - D_BOBA                        # -3.0%

assert ALL_SH == 8 and BOBA_SH / ALL_SH == 0.75
assert (EPS0, EPS_NO, EPS_SYN, EPS_HALF) == (2.0, 1.875, 2.125, 2.0)
assert abs(EPS_SYN / EPS0 - 1 - 0.0625) < 1e-9 and abs(EPS_NO / EPS0 - 1 + 0.0625) < 1e-9
assert DEAL == 80 and abs(PREMIUM - 1 / 3) < 1e-9 and abs(FEE / DEAL - 0.0375) < 1e-9
assert round(P2, 2) == 36.10 and round(PEARL1, 2) == 18.05 and round(PEARL2, 2) == 16.61
assert round(D_PEARL * 100, 1) == -8.0 and round(D_SPREAD * 100, 1) == -3.0
assert abs((1 + D_BOBA) * (0.92 / 0.95) - 1 - D_PEARL) < 1e-9          # 两刀相乘 = 总跌幅
STORES, PACE, GOAL = 4200, 600, 8000
assert STORES + 4 * PACE == 6600 and (GOAL - STORES) / 4 == 950

SCEN = [  # 股价推演：示意 EPS × 倍数
    dict(name="顺利整合", prob=35, eps=EPS_SYN, lo_x=20, hi_x=22, color="green"),
    dict(name="整合平平", prob=45, eps=EPS_HALF, lo_x=18, hi_x=20, color="blue"),
    dict(name="交易告吹", prob=20, eps=EPS0, lo_x=15, hi_x=17, color="red"),
]
for s in SCEN:
    s["lo"], s["hi"] = s["eps"] * s["lo_x"], s["eps"] * s["hi_x"]
EXPECT = sum(s["prob"] / 100 * (s["lo"] + s["hi"]) / 2 for s in SCEN)
assert round(EXPECT, 1) == 39.1

A3 = ["blue"] * 6
AL = ["A", "A", "B", "B", "C", "C"]

# ============================================================ ② 图
# ---- 主线：核心矛盾
m = Canvas(760, 272, "mainline")
m.text(150, 30, "收购前", size=16, bold=True).text(612, 30, "收购后", size=16, bold=True)
m.pie(92, 122, 52, A3, AL)
m.coins(166, 88, 12, "green", cols=4)
m.text(150, 204, "6 块饼 · 12 枚币", size=13.5).text(150, 228, "每块分 2 枚", size=15, bold=True, color="blue")
m.pie(552, 122, 52, A3 + ["orange"] * 2, AL + ["D", "D"])
m.coins(628, 80, 15, "green", cols=4)
m.coins(628, 80, 2, "orange", cols=4, start=15)
m.text(612, 204, "8 块饼 · 17 枚币", size=13.5).text(612, 228, "每块分 2.125 枚", size=15, bold=True, color="blue")
m.rect(300, 100, 160, 44, "ink", "hl").text(380, 128, "每块分到几枚币？", size=15, bold=True)
m.arrow(380, 96, 380, 62, "green", cls="bold").text(380, 50, "利润的饼变大：12 → 17", size=13.5, color="green", bold=True)
m.arrow(380, 148, 380, 182, "orange", cls="bold").text(380, 202, "分饼的人变多：6 → 8", size=13.5, color="orange", bold=True)
m.arrow(244, 122, 294, 122).arrow(466, 122, 494, 122)
m.text(744, 262, "示意值：1 块饼 = 1 亿股，1 枚币 = $1 亿年利润", size=12, anchor="end", color="ink2")

# ---- 核心竞争力：三道护城河
moat = Canvas(760, 214, "moat")
for r, lab, dash in ((130, "① 门店密度：4,200 家", False), (190, "② 自己的珍珠：100% 自供", False),
                     (250, "③ 3,000 万会员（最容易被抢）", True)):
    moat.path("M%d 196A%d %d 0 0 1 %d 196" % (380 - r, r, r * 0.6, 380 + r), "blue", dash=dash, cls="bold")
    moat.text(380, 196 - r * 0.6 - 8, lab, size=13.5, bold=True)
moat.shop(380, 194, w=62, h=40, color="green", label="BOBA")

# ---- 远期规划：目标 vs 现在的速度
v = Canvas(760, 250, "vision")
base, k = 204, 150 / GOAL
v.line(70, base, 700, base)
v.bar(130, base - STORES * k, 120, STORES * k, "green").text(190, base - STORES * k - 9, "4,200 家", size=14, bold=True)
v.bar(330, base - 6600 * k, 120, 6600 * k, "orange").text(390, base - 60, "6,600 家", size=14, bold=True)
v.rect(330, base - GOAL * k, 120, (GOAL - 6600) * k, "red", "red", dash=True, r=3)
v.text(390, base - GOAL * k - 9, "还差 1,400 家", size=13.5, bold=True, color="red")
v.bar(530, base - GOAL * k, 120, GOAL * k, "orange", dash=True).text(590, base - GOAL * k - 9, "8,000 家", size=14, bold=True)
v.text(190, base + 24, "2026 现在", size=13).text(390, base + 24, "2030 · 按现在的速度", size=13)
v.text(590, base + 24, "2030 · 管理层目标", size=13)

# ---- 8 张两格漫画
c1 = Comic("珍珠年年涨价，受制于人", "直接买下珍珠工厂")
c1.shop(70, 172, label="BOBA").shop(210, 172, color="orange", label="PEARL")
c1.arrow(170, 150, 112, 150, "orange").text(140, 102, "年年涨价", size=12.5, color="orange", bold=True)
c1.rect(322, 84, 196, 98, "green", None, dash=True, r=14).text(420, 72, "合成一家", size=13, bold=True, color="green")
c1.shop(376, 172, label="BOBA").shop(464, 172, color="orange", label="PEARL")

c2 = Comic("金库凑不出 $80 亿", "多切 2 块新饼给 D")
c2.rect(36, 78, 96, 96, "blue", None, r=6).coins(50, 132, 4, "blue", cols=4).text(84, 100, "现金", size=13, bold=True)
c2.doc(178, 84, 62, 50, rows=0).text(209, 115, "$80 亿", size=14, bold=True).text(209, 158, "要价", size=12.5, color="ink2")
c2.cross(152, 124, 8)
c2.pie(372, 118, 50, A3 + ["orange"] * 2, AL + ["D", "D"])
c2.arrow(430, 108, 472, 108, "orange").person(506, 80, "D", "orange", "happy").text(506, 164, "新股东", size=12.5, color="ink2")

c3 = Comic("8 块分 15 枚，每块变少", "省下中间价，多出 2 枚")
c3.pie(60, 108, 32, ["blue"] * 8).text(60, 166, "8 块饼", size=12.5, color="ink2")
c3.coins(116, 74, 15, "green", cols=5).text(157, 144, "15 枚币", size=12.5, color="ink2")
c3.text(190, 176, "每块 1.875 枚", size=13.5, bold=True, color="red")
c3.pie(340, 108, 32, ["blue"] * 8).text(340, 166, "8 块饼", size=12.5, color="ink2")
c3.coins(396, 66, 15, "green", cols=5).coins(396, 66, 2, "orange", cols=5, start=15)
c3.text(437, 153, "17 枚币", size=12.5, color="ink2").text(470, 178, "每块 2.125 枚", size=13.5, bold=True, color="green")

c4 = Comic("有人说赚，有人说亏", "只看一个数：每股盈利")
c4.bubble(26, 56, 104, 36).text(78, 79, "总利润多了", size=12.5).person(60, 116, "A", "blue", "happy")
c4.bubble(148, 56, 104, 36).text(200, 79, "我的份变小", size=12.5).person(190, 116, "B", "blue", "sad")
c4.line(308, 124, 532, 124, cls="bold")
for x, val, lab, col in ((340, "$1.875", "没协同", "red"), (420, "$2.00", "收购前", "ink"), (500, "$2.125", "有协同", "green")):
    c4.line(x, 112, x, 136, col, cls="bold").text(x, 100, val, size=13.5, bold=True, color=col).text(x, 160, lab, size=12.5, color="ink2")
c4.text(420, 70, "每股盈利", size=13, bold=True)

c5 = Comic("发几块新饼，谈不拢", "合同写死：2 股换 1 股")
c5.bubble(26, 56, 100, 36).text(76, 79, "只给 1 块", size=12.5).person(60, 116, "A", "blue", "flat")
c5.bubble(152, 56, 100, 36, tail="right").text(202, 79, "我要 3 块", size=12.5).person(214, 116, "D", "orange", "sad")
c5.bar(314, 88, 34, 22, "orange").bar(314, 120, 34, 22, "orange").text(331, 170, "2 股 PEARL", size=12.5)
c5.arrow(356, 116, 388, 116)
c5.doc(394, 82, 56, 68, rows=0).text(422, 112, "合同", size=12.5, color="ink2").text(422, 134, "× 0.5", size=14, bold=True)
c5.arrow(456, 116, 484, 116).bar(490, 104, 36, 24, "blue").text(506, 170, "1 股 BOBA", size=12.5)

c6 = Comic("审批没过，不敢付全价", "打个 5% 的折再买")
c6.doc(34, 82).text(56, 160, "审批中", size=12.5, color="ink2")
c6.bubble(112, 64, 136, 36).text(180, 87, "万一不批呢？", size=12.5).person(170, 118, "C", "blue", "sad")
c6.bar(304, 62, 232, 28, "blue").text(420, 81, "换到的 BOBA 值 $19.00", size=12.5, bold=True)
c6.bar(304, 112, 220, 28, "blue").rect(524, 112, 12, 28, "red", "red", dash=True, r=2)
c6.text(414, 131, "PEARL 市价 $18.05", size=12.5, bold=True)
c6.curve(486, 168, 529, 146, bend=-0.3, stroke="red").text(446, 174, "价差 5%", size=13, bold=True, color="red")

c7 = Comic("没人接盘，折扣越拉越大", "E 买 PEARL、卖 BOBA")
c7.bubble(26, 60, 92, 36).text(72, 83, "谁来接？", size=12.5).person(58, 120, "D", "orange", "sad")
for x, hgt, lab in ((150, 24, "5%"), (188, 44, "6%"), (226, 68, "8%")):
    c7.rect(x, 172 - hgt, 26, hgt, "red", "red", dash=True, r=3).text(x + 13, 164 - hgt, lab, size=12.5, bold=True, color="red")
c7.person(420, 78, "E", "card", "happy")
c7.rect(300, 96, 76, 30, "blue", "blue").text(338, 116, "买 PEARL", size=12.5, bold=True)
c7.rect(464, 96, 76, 30, "blue", None, dash=True).text(502, 116, "卖 BOBA", size=12.5, bold=True)
c7.arrow(402, 112, 381, 112).arrow(438, 112, 459, 112)
c7.text(420, 174, "等交割，价差归零", size=13, bold=True, color="green")

c8 = Comic("一方反悔，另一方白等", "反悔的一方赔 $3 亿")
c8.doc(44, 80, stroke="red").cross(66, 107, 16).text(66, 160, "交易取消", size=12.5, color="red")
c8.person(190, 100, "D", "orange", "sad").text(190, 180, "白等半年", size=12.5, color="ink2")
c8.doc(308, 80).text(330, 160, "合同", size=12.5, color="ink2")
c8.coins(376, 98, 3, "blue", cols=3).text(400, 134, "$3 亿", size=13.5, bold=True, color="blue")
c8.arrow(432, 105, 470, 105, "blue").person(504, 76, "D", "orange", "happy").text(504, 160, "拿到赔偿", size=12.5, color="ink2")

# ============================================================ ③ 拼页面
p = Page(
    "波波茶收购珍珠工厂：<em>基本面变了吗？</em>",
    "一家奶茶连锁用“印新股”的办法买下自己的珍珠供应商。这页用 8 个概念、6 块饼、12 枚币，把这桩买卖从头讲到尾。",
    notice="⚠ <b>演示页：波波茶 BOBA、珍珠工厂 PEARL 都是虚构公司</b>，所有数字都是示意值，只为展示 stock-html 生成的页面长什么样。",
)

p.mainline(
    "这笔收购是一场拔河：<b>利润的饼变大</b>，但<b>分饼的人也变多</b>，每块饼最后多分还是少分，决定这桩买卖值不值。",
    m, kind="核心矛盾",
    note="固定角色：A、B、C = BOBA 的三位老股东；D = 原 PEARL 股东（收购后变成新股东）；E = 套利者。饼 = 股份，币 = 年利润。")

p.checkup([
    ("ok", "<b>主业没变：</b>老店年利润仍是 $12 亿（每股 $2.00），这次公告没有下调。"),
    ("ok", "<b>算上协同是增厚的：</b>每股盈利 $2.00 → $2.125(+6.25%)，口径 = (12 + 3 + 2) ÷ 8 亿股。"),
    ("mid", "<b>股份变多：</b>6 亿股 → 8 亿股，老股东占比 100% → 75%。"),
    ("mid", "<b>协同只是目标：</b>管理层说每年省 $2 亿；保本线是 $1 亿，低于它每股盈利就比收购前少。"),
    ("bad", "<b>新风险：</b>审批还没过，市场给的折扣（价差）已从 5% 扩大到 8%。"),
    ("bad", "<b>股价：</b>$40.00 → $36.10(−9.75%)，公告日跌 5%，今天再跌 5%。"),
], small="基本面变了吗？")

p.section(
    "核心竞争力：三道护城河",
    "结论：BOBA 真正难抄的只有前两道——<b>门店密度</b>和收购后<b>自己做珍珠</b>。第三道会员最浅，对手一张优惠券就能跨过来。",
    canvas=moat, role="moat",
    tiles=[
        ("① 门店密度", "4,200 家店，同城平均 1.2 公里一家，外卖 20 分钟送到。", "弱点：70% 是加盟店，品控靠抽查。"),
        ("② 自己的珍珠", "收购后珍珠 100% 自供，每杯成本省 $0.10（= $2 亿 ÷ 20 亿杯）。", "弱点：珍珠只占原料成本的 30%。"),
        ("③ 3,000 万会员", "会员复购贡献 65% 的收入。", "弱点：换一家店，只需要一张优惠券。"),
    ])

p.chain([
    ("并购", "要付 $80 亿"), ("换股收购", "老股东被稀释"), ("协同效应", "值不值说不清"), ("每股盈利增厚", "全看发多少新股"),
    ("换股比例", "没交割，价值悬空"), ("并购价差", "折扣没人接"), ("并购套利", "交易一黄就大亏"), ("分手费", "只补得回一小块"),
])

p.card("并购", "M&A · Mergers and Acquisitions", "一家公司把另一家买下来，两家变一家。", c1,
       "一步到位拿到对方的工厂和产能，不用再看供应商脸色。", "要付 $80 亿，比 PEARL 公告前的市价贵 33%（这叫溢价）。", "done")
p.card("换股收购", "Stock-for-stock deal", "不付现金，而是印新股票交给对方股东当货款。", c2,
       "一分现金不花，就付清了 $80 亿。", "饼从 6 块切成 8 块，A、B、C 的占比从 100% 降到 75%。", "done")
p.card("协同效应", "Synergy", "两家合并后，比各干各的多赚（或少花）的那部分钱。", c3,
       "利润的饼变大，把被稀释掉的那部分补回来。", "$2 亿只是管理层的目标，可能迟到，也可能落空。", "redo")
p.card("每股盈利增厚", "EPS accretion", "合并后每股盈利比合并前高叫增厚，低了叫摊薄（dilution）。", c4,
       "把“划不划算”变成一个能算的数：$2.00 → $2.125，增厚 6.25%。", "它只看一年的利润，看不到风险，还可以靠乐观假设“算”出来。", "redo")
p.card("换股比例", "Exchange ratio", "合同里写死：每 1 股 PEARL 换 0.5 股 BOBA。", c5,
       "新股数量锁定：4 亿股 × 0.5 = 2 亿股，不用再扯皮。", "比例固定、价钱不固定：BOBA 跌多少，D 到手的就少多少。")
p.card("并购价差", "Merger spread", "PEARL 的市价，比“按比例换到的 BOBA 价值”便宜的那一截。", c6,
       "给“交易可能告吹”标了价，愿意担风险的人才肯接盘。", "PEARL 的股价从此绑在 BOBA 身上，还要多扣一层折扣。")
p.card("并购套利", "Merger arbitrage", "买入被收购方、同时卖空收购方，赚交割时价差归零的钱。", c7,
       "有人专门收下这份风险，价差被压小，D 想卖随时能卖。", "套利者要卖空 BOBA，公告后 BOBA 的股价多了一层卖压。")
p.card("分手费", "Break-up fee", "谁反悔，谁赔对方一笔事先约定的钱（这里是 $3 亿）。", c8,
       "反悔有了成本，双方都不敢随便退出。", "$3 亿只占交易额的 3.75%，真黄了远远补不回股价的损失。")

p.section(
    "技术规划路线：把一杯茶的成本压下去",
    "结论：三级台阶只干一件事——减少一杯奶茶里的人工和原料成本。越往右越不确定：第三级目前只有试点，没有时间表。",
    canvas=roadmap([
        ("现在 · 2026", "半自动门店", ["煮珍珠机已铺 1,500 家店", "扫码点单占 80%"]),
        ("下一步 · 2027", "中央工厂直供", ["PEARL 工厂并入排产", "珍珠配送 48 → 24 小时"]),
        ("以后 · 2028+", "无人制茶站", ["一台机器顶 2 名店员", "仅试点，未公布时间表"]),
    ]), role="roadmap")

p.section(
    "远期规划：2030 年 8,000 家店",
    "结论：这是<b>目标</b>，不是业绩指引。按现在每年净增 600 家，2030 年只有 6,600 家；要达标，每年得开 950 家。",
    canvas=v, role="vision",
    note="算法：4,200 + 600 × 4 = 6,600;(8,000 − 4,200) ÷ 4 = 950。门店数为示意值。")

p.section(
    "隐藏危机：公告里没写的事",
    "结论：最该盯的不是最吓人的，而是<b>又可能、又疼</b>的那个——协同落空。审批被否杀伤最大，但价差已经在替你盯着；真正藏着的是加盟店食品安全和口味变迁，公告里一个字都没有。",
    canvas=risk_matrix([
        dict(name="审批被否", p=.30, impact=.90),
        dict(name="协同落空", p=.58, impact=.60),
        dict(name="加盟店食品安全", p=.20, impact=.72, color="orange"),
        dict(name="再次增发", p=.36, impact=.26, color="orange"),
        dict(name="珍珠不再流行", p=.14, impact=.46, color="orange"),
    ]), role="risks",
    table=(["危机", "为什么容易被忽略", "预警信号（盯哪个数）"], [
        ["审批被否", "公告只写“预计通过”", "价差超过 10%；监管发出补充问询"],
        ["协同落空", "$2 亿是目标，不进财报", "毛利率连续两季没有改善"],
        ["加盟店食品安全", "70% 的门店不归公司直管", "抽检不合格率、单店投诉量"],
        ["再次增发", "开到 8,000 家店需要钱", "账上现金少于两个季度的资本开支"],
        ["珍珠不再流行", "自供等于把鸡蛋放进一个篮子", "含珍珠饮品占销量的比重下滑"],
    ]))

p.section(
    "关键时间节点",
    "结论：接下来只有两个日子是写死的——<b>12/15 股东投票</b>和 <b>3/31 审批期限</b>。其余都是“预计”，以公司公告为准。",
    canvas=timeline([
        dict(date="10/20", name="宣布收购"),
        dict(date="11/11", name="今天", now=True),
        dict(date="12/15", name="股东大会投票"),
        dict(date="预计 1 月下旬", name="Q4 财报（未公告）", sure=False),
        dict(date="3/31", name="审批最后期限"),
        dict(date="预计 Q2", name="交割", sure=False),
    ]), role="timeline",
    table=(["什么时候", "什么事", "看什么", "日期确认了吗"], [
        ["12/15", "股东大会投票", "赞成票是否过 2/3", "已确认（公司公告）"],
        ["预计 1 月下旬", "Q4 财报", "$2 亿协同有没有拆成带时间表的项目", "未确认（去年是 1/28）"],
        ["3/31", "反垄断审批期限", "通过 / 附条件通过 / 否决", "已确认（合同约定）"],
        ["预计 Q2", "交割", "价差是否收敛到 0", "未确认，取决于审批"],
    ]))

p.section(
    "股价推演：三条路",
    "结论：BOBA 现价 $%.2f，最可能的一条路是“整合平平”（45%%），落在 $36–40，也就是原地附近。三条路按概率加权的中点约 $%.1f。" % (P2, EXPECT),
    canvas=paths_chart(
        [("7月", 34), ("8月", 36), ("9月", 39), ("10月初", 41), ("公告前", BOBA_P0), ("公告日", P1), ("今天", P2)],
        SCEN, h=360),
    role="paths",
    table=(["路径", "需要发生什么", "示意 EPS × 倍数", "价格区间", "概率"], [
        [s["name"], need, "$%s × %d–%d 倍" % (("%.3f" % s["eps"]).rstrip("0").rstrip(".") if s["eps"] % 1 else "%.2f" % s["eps"], s["lo_x"], s["hi_x"]),
         "$%.2f – %.2f" % (s["lo"], s["hi"]), "%d%%" % s["prob"]]
        for s, need in zip(SCEN, ["审批通过，$2 亿协同全部兑现", "审批通过，协同只兑现一半（$1 亿）", "审批被否，BOBA 赔 $3 亿分手费"])
    ]),
    after="<b>下一份财报后的机会：</b>看点是管理层有没有把 $2 亿协同拆成带时间表的具体项目。审批通过、且首季协同进度达标，是右侧确认信号；股价跟着大盘回落、但审批和协同都没变坏，才谈得上分批。两种情况都先回到上面这张表，重算 EPS × 倍数。",
    note="示意 EPS = （BOBA 利润 + PEARL 利润 + 兑现的协同） ÷ 8 亿股。概率是主观估计，不是预测；公司为虚构。")

p.section(
    "一把尺子：每股盈利 × 倍数",
    "结论：股价 = 每股盈利 × 倍数，所以任何消息只问两件事——它动了<b>每股盈利</b>，还是动了<b>倍数</b>。同一条虚线上股价相同；右边的量杯是“确定性”，审批悬着的时候水位下降，倍数就跟着掉。",
    canvas=ruler_chart(
        [dict(name="公告前 $40", x=EPS0, y=20, color="blue", dx=-12, dy=4, anchor="end"),
         dict(name="今天 $36.10", x=EPS0, y=P2 / EPS0, color="ink", dx=-12, dy=8, anchor="end"),
         dict(name="顺利整合", x=EPS_SYN, y=21, color="green", dx=12, dy=4),
         dict(name="整合平平", x=EPS_HALF, y=19, color="blue", dx=12, dy=4),
         dict(name="交易告吹", x=EPS0, y=16, color="red", dx=12, dy=4)],
        xr=(1.7, 2.3), yr=(14, 24), iso=(32, 36, 40, 44, 48),
        gauge=dict(label="确定性", level=.42, was=.8, hi="高", lo="低")),
    role="ruler",
    table=(["办法", "改善哪个指标", "牺牲哪个指标"], [
        ["换股收购", "确定性（不用借钱）", "每股盈利（股数多了 33%）"],
        ["协同效应", "每股盈利（多 $0.25）", "确定性（只是目标）"],
        ["换股比例", "确定性（新股数量锁死）", "倍数（对价跟着股价浮动）"],
        ["并购套利", "确定性（价差被压小）", "倍数（卖空带来卖压）"],
        ["分手费", "确定性（反悔有成本）", "每股盈利（黄了一次性少 $0.50）"],
    ]),
    note="多 $0.25 = 2.125 − 1.875；少 $0.50 = $3 亿 ÷ 6 亿股。")

p.section(
    "零基础版：为什么 PEARL 跌得比 BOBA 还多？",
    "结论：PEARL 的股价 = BOBA 股价 × 0.5 ×（1 − 价差），所以它要挨两刀——BOBA 自己跌一刀，价差拉大再补一刀。今天 BOBA 跌 5%,PEARL 却跌了 8%，多出来的 3 个点全部来自价差。",
    canvas=waterfall([("① BOBA 下跌", D_BOBA * 100, "red"), ("② 价差 5% → 8%", D_SPREAD * 100, "red")], total_label="PEARL 合计"),
    steps=[
        "昨天：BOBA $38.00，价差 5% → PEARL = 38.00 × 0.5 × (1 − 5%) = <b>$18.05</b>",
        "今天 BOBA 跌 5%%:38.00 × 0.95 = <b>$36.10</b>。如果价差不变，PEARL = 36.10 × 0.5 × 0.95 = $%.2f(也跌 5%%)" % PEARL_FLAT,
        "但审批传出坏消息，价差从 5% 扩大到 8%:PEARL = 36.10 × 0.5 × (1 − 8%) = <b>$16.61</b>",
        "合计：16.61 ÷ 18.05 − 1 = <b>−8.0%</b>，其中 −5.0% 来自 BOBA,−3.0% 来自价差",
    ],
    table=(["", "做法 A：直接买 BOBA", "做法 B：买 PEARL 等换股"], [
        ["今天花多少", "$36.10 买 1 股 BOBA", "$%.2f 买 2 股 PEARL" % (2 * PEARL2)],
        ["交割后手里有", "1 股 BOBA", "1 股 BOBA(2 × 0.5)"],
        ["便宜了多少", "—", "便宜 8%%($%.2f)" % (P2 - 2 * PEARL2)],
        ["交易告吹时", "仍然拿着 BOBA", "PEARL 可能跌回公告前的 $15 附近（示意，约 −%.1f%%）" % ((1 - PEARL_P0 / PEARL2) * 100)],
        ["你在赌什么", "BOBA 的生意", "审批会通过"],
    ]),
    role="eli5")

p.route([
    Stop("先懂倍数", "尺子的纵轴；知道 P/E 是股价除以每股盈利。", "10 分钟",
         "https://en.wikipedia.org/wiki/Price%E2%80%93earnings_ratio", "Wikipedia · Price–earnings ratio", verified=True),
    Stop("再算增厚", "亲手算一遍第 3、4 张卡：合并后每股盈利升还是降。", "20 分钟",
         "https://en.wikipedia.org/wiki/Accretion/dilution_analysis", "Wikipedia · Accretion/dilution analysis", verified=True),
    Stop("看懂价差", "第 6、7 张卡的完整版：套利者怎么赚钱、什么时候亏。", "20 分钟",
         "https://en.wikipedia.org/wiki/Risk_arbitrage", "Wikipedia · Risk arbitrage", verified=True),
    Stop("去读一手公告", "真实的收购都会发 8-K；学会从公告里找换股比例和分手费。", "30 分钟",
         "https://en.wikipedia.org/wiki/Form_8-K", "Wikipedia · Form 8-K", verified=True),
], intro="四站，大约一个半小时。链接都已打开核实过内容。")

p.sources([
    ("本页公司、股价、财务数字全部为虚构，由本目录的 boba_merger.py 计算生成（脚本开头有全部算式和断言）", None),
    ("Wikipedia · Price–earnings ratio", "https://en.wikipedia.org/wiki/Price%E2%80%93earnings_ratio"),
    ("Wikipedia · Accretion/dilution analysis", "https://en.wikipedia.org/wiki/Accretion/dilution_analysis"),
    ("Wikipedia · Risk arbitrage", "https://en.wikipedia.org/wiki/Risk_arbitrage"),
    ("Wikipedia · Form 8-K", "https://en.wikipedia.org/wiki/Form_8-K"),
])

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "boba-merger.html"
    p.save(out)
