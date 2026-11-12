---
name: stock-html
description: "把一只股票、一份财报、一条并购/重大新闻，或任何学习资料（文章、论文、技术文档、研报、课程笔记），做成一遍就能看懂的卡通手绘图解 HTML 页面（单文件、深浅两套主题、可发布为 Artifact）。股票类默认产出完整图解报告：体检单、核心竞争力、技术规划路线、远期规划、隐藏危机、关键时间节点、股价推演、估值尺子。当用户说\"图解一下\"\"做成图解页面\"\"帮我一遍看懂\"\"ELI5 这份资料\"\"零基础讲讲这个\"\"分析一下这只股票 / 这份财报 / 这条新闻\"\"基本面变了吗\"\"这家公司的护城河、风险、催化剂是什么\"，或要求把文章、论文、财报、技术文档做成可视化学习页时使用。Also use for English requests like \"explain this stock / earnings report / merger visually\", \"make an illustrated explainer page\", \"ELI5 this filing\"."
---

# stock-html：一遍看懂的手绘图解页

把材料做成**一个单文件 HTML 页面**：方格纸 / 黑板两套手绘主题，固定角色的两格漫画，全部数字可复算。两种用法：

- **股票报告**(`kind="stock"`，默认)：一只股票、一份财报、一条并购或重大新闻 → 一份完整的图解报告。
- **通用学习页**(`kind="general"`)：文章、论文、技术文档、课程笔记 → 主线 + 概念依赖链 + 漫画卡片 + 学习路线。

本目录自带工具箱，**不要从零手写 HTML**:

| 文件 | 干什么 |
|---|---|
| `scripts/sketch.py` | 画布、两格漫画、现成图表、整页拼装；`save()` 时自动做离线版面检查 |
| `scripts/blocks.py` | 半成品积木：主线图、护城河、远期对账图、三种两格漫画版式、股价推演表——一次做多份报告时用 |
| `scripts/verify.py` | 用无头 Chrome 真实渲染，读页面内置自检结果，分段截图 |
| `assets/template.html` | 页面模板：两套主题、抖动滤镜、印章进度、内置自检脚本 |
| `examples/boba_merger.py` | **完整参考写法**（虚构公司的个股报告），开工前先读一遍 |
| `references/stock-report.md` | 股票报告每一节怎么写、数据纪律 |
| `references/visual-style.md` | 视觉规范、画布坐标、手写 SVG 的规矩 |
| `references/qa.md` | 三层自检、看图要点、没有 Chrome 时的备用办法 |

## 三条不可妥协

1. **读者零基础。** 每个术语第一次出现时用一句话解释，括号里给英文原词。禁止"如你所知""显而易见""不难理解"。
2. **先说结论，再说原理。** 每一节第一句必须是结论，不是背景铺垫。
3. **数字不能凭印象。** 所有数字先核实、先用脚本算平，再画图。推算值标"示意"，概率标"主观估计，不是预测"。

## 工作流程

1. **读完全部材料**——用户给的文件、截图、链接，一个不落。
2. **联网核实**——一手来源优先（公司公告、8-K、新闻稿、财报），把每个要用的数字落地。细则见 `references/stock-report.md` 的"数据纪律"。
3. **写 build 脚本，数字放最上面**——所有输入和推算写成变量，用 `assert` 互相对账（涨跌幅分解、价差、增厚/摊薄、倍数 × EPS）。算不平不许往下画。
4. **排概念依赖链**（8–13 个概念）——按"后一个概念是为了解决前一个概念带来的问题"排，**不按材料原顺序**。某个概念说不出它在解决上一个的什么问题，就是排错了。
5. **拼页面**——照 `examples/boba_merger.py` 的写法：
   ```python
   import sys; sys.path.insert(0, "<本 skill 目录>/scripts")
   from sketch import *
   p = Page("标题", "副标题")            # 默认 kind="stock"
   p.mainline(...); p.checkup(...); p.section(..., role="moat"); p.chain(...); p.card(...)  # …
   p.save("out.html")                     # 写文件 + 离线预检,有 ERROR 就改到没有
   ```
6. **真实渲染检查**——`python3 scripts/verify.py out.html --shots shots/`。必须看到 `[CHECK light] PASS` 和 `[CHECK dark] PASS`，然后**逐张看截图**（浅色、深色至少各看两段）。细则见 `references/qa.md`。
7. **交付**——环境里有 Artifact 发布工具就发布（发布后读控制台，确认两个主题都是 PASS）；没有就把 HTML 文件交给用户。
8. **回复用户**——先用 2–3 句直接回答他的问题（比如"基本面变了吗"），再用 5–8 个要点说明页面里有什么，注明和预期不同的地方（日期未确认、反推的数字、字体回退），最后列来源。

## 股票报告的默认结构

**下面每一节默认都要有**(`Page.save()` 会对缺失的节报警)。这是"至少要有"，不是"只能有"：材料里还有别的重点（估值与同行对比、管理层与资本配置、现金流与负债、客户集中度……）就再加 `section()`。每节正文 ≤ 4 句，以图为主。

| # | 小节 | 怎么调用 | 必须回答的问题 | 用什么图 |
|---|---|---|---|---|
| 1 | 主线 | `mainline()` | 这件事到底在干什么？（主循环 / 流水线 / 核心矛盾 三选一） | 一句话 + 一张图 |
| 2 | 体检单 | `checkup()` | 基本面变了吗？每行带数字和口径 | ✓ 绿勾 / — 橙横 / ✗ 红叉 |
| 3 | **核心竞争力** | `section(role="moat")` | 哪 2–3 件事别人真的抄不走？证据是哪个数？弱点在哪？ | 护城河图 + `tiles` |
| 4 | 概念依赖链 | `chain()` | 看懂这家公司 / 这条新闻要先懂哪 8–13 个概念？ | 蛇形流程图 |
| 5 | 概念卡片 | `card()` × N | 每个概念：没有它时的烦恼 → 它的办法 → 解决了什么、代价是什么 | 两格漫画 |
| 6 | **技术规划路线** | `section(role="roadmap")` | 现在做到哪、下一步是什么、哪些只是愿景？ | `roadmap()` 台阶图 |
| 7 | **远期规划** | `section(role="vision")` | 管理层 3–5 年要去哪？按现在的速度到得了吗，差多少？ | 目标 vs 现速对比图 |
| 8 | **隐藏危机** | `section(role="risks")` | 公告和多头叙事里没写的 4–6 件事；各自的预警信号是哪个数？ | `risk_matrix()` + 预警表 |
| 9 | **关键时间节点** | `section(role="timeline")` | 未来 6–12 个月哪几天会出结果？哪些日期还没确认？ | `timeline()` + 日程表 |
| 10 | **股价推演** | `section(role="paths")` | 2–3 条路各需要发生什么、落在什么价位、主观概率多少？ | `paths_chart()` + 推演表 |
| 11 | 尺子 | `section(role="ruler")` | 衡量好坏的 2–3 个指标；每个办法改善哪个、牺牲哪个？ | `ruler_chart()` + 对照表 |
| 12 | 零基础版（按需） | `section(role="eli5")` | 最反直觉的那个机制，一步一步带算式 | 瀑布图 + 步骤 + 对比表 |
| 13 | 学习路线 | `route()` | 3–4 站：为什么去、去多久、链接 | 地铁线路图 |
| — | 页脚 | `sources()` | 全部来源 + "仅作学习用途，不构成投资建议" | — |

每一节的写法、常见空话和反例见 **`references/stock-report.md`(写股票报告前必读)**。

## 通用学习页的结构

`Page(..., kind="general")`：主线 → 概念依赖链 → 概念卡片 → 尺子（这个领域衡量好坏的 2–3 个指标画在同一张图上）→ 零基础版（按需）→ 学习路线。没有体检单、股价推演和免责声明。

## 贯穿全页的规矩

- **固定角色。** 全页所有图用同一组角色，不同概念里不换人。股票类默认：A、B、C 三位老股东 + D 一位新股东；饼 = 股份，币 = 利润。在主线图下面用一行小字交代角色。
- **数字缩小版。** 把 9.21 亿股画成 6 块饼、把 $10 亿利润画成 10 枚币；比例必须和真实数据一致，图上标"示意值"。
- **概念卡片只写两行**:"解决了什么"和"代价是什么"。代价不许留空、不许写"基本没有代价"——找不到代价就是没想清楚。
- **固定颜色语义**（全页一致）：绿 = 正在进行的（业务、利润）；橙 = 新来的（新事件、新股东）；蓝 = 存起来的（股份、现金、价值）；红色虚线 = 作废 / 被释放的（损失）。印章用紫色。

## 硬性要求（发布前逐条过）

1. 每格漫画说明文字 ≤ 15 个字（连数字和符号一起数；英文页 ≤ 32 字符）。
2. 文字绝不压边框、绝不互相重叠。
3. 以图为主，正文每节 ≤ 4 句。
4. 所有图是手写的内联 SVG(用 `sketch.py` 生成)。不用 Chart.js / D3 / Mermaid。
5. CSS、JS、SVG 全部内联在一个 HTML 文件里；不加任何外链（包括 Google Fonts——部分 Artifact 环境的 CSP 会拦）。
6. 文字不进抖动滤镜、不加 transform(`Canvas.text()` 已经保证；手写 SVG 时自己注意)。
7. 学习路线的链接**必须用抓取工具打开核实**，内容对得上才写 `verified=True`。被拦截或打不开就换一个，或不给 `url`(页面会显示"需自行搜索")。**编造链接是这个技能最严重的失败。**
8. 不提用户的持仓和期权，只分析股票本身；不给买卖指令。
9. `verify.py` 两个主题都 PASS，并且看过截图。

## 工具箱速查

```python
# 画布:颜色只用语义名 ink / ink2 / green / orange / blue / red / purple
c = Canvas(760, 300, "名字")                    # 大图 760 宽,字号 ≥ 12
c.rect / line / arrow / curve / circle / path / poly / bar      # fill="green" 浅色,"green!" 实心
c.text(x, y, "文字", size=14, anchor="middle", color="ink", bold=False)
c.person(cx, top, "A", "blue", mood="happy")    # 固定角色小人(约 30×60)
c.pie(cx, cy, r, ["blue"]*6 + ["orange"]*2, labels)   c.coins(x, y, 12, "green", cols=4)
c.shop(cx, base, label="BOBA")   c.doc(x, y)   c.bubble(x, y, w, h)   c.tick / cross / minus

# 两格漫画:560×232;左格中心 x=140,右格中心 x=420;你的绘图区 y 44–188
k = Comic("左格说明 ≤15 字", "右格说明 ≤15 字")

# 现成图表(都返回 Canvas)
snake(nodes)   metro(stations)   timeline(events)   roadmap(stages)   risk_matrix(items)
paths_chart(history, scenarios)   ruler_chart(points, xr, yr, iso, gauge)   waterfall(steps)

# 页面
p = Page(title, subtitle, kind="stock", notice=None)
p.mainline(一句话, canvas, kind="核心矛盾", note="固定角色:…")
p.checkup([("ok" | "mid" | "bad", "带数字的一行"), ...])
p.chain([(概念名, 它带来的新问题), ...])
p.card(name, en, definition, comic, solves, cost, stamp="next" | "redo" | "done")
p.section(title, prose, canvas=, table=(表头, 行), steps=[…], tiles=[…], after=, note=, role=)
p.route([Stop(name, why, time, url, link_text, verified=True), ...])
p.sources([(标题, url), ...]);  p.save("out.html")
```

英文页面：在创建任何 `Comic` / `Page` 之前调用 `set_lang("en")`。每个函数的参数细节直接看 `scripts/sketch.py` 里的 docstring。

**一次做多份报告**（比如一个 ETF 的前十大成分股）时，用 `scripts/blocks.py` 的积木，每份报告只需写数字和文案：

```python
from blocks import *          # 同时导入 sketch 的全部工具
m  = mainline_tug(左标题, [(标签, 值, 是否指引)×3], 单位注, 问题, 副问题, [(力量, 颜色)×3], 右标题, [(日期, 股价), ...], "−6%")
mo = moat(["① 最深", "② 次之", "③ 最浅"], "TICK")
vi = vision([(值, 标签1, 标签2, 颜色, 虚线)×3], gap_between=(1, 2), note="算法…")
c1 = C_bars(左说明, 右说明, [(标签, 值, 颜色)], [(标签, 值, 颜色)], lnote=, rnote=, fmt="%g")   # 前后对比柱
c2 = C_talk(左说明, 右说明, "A", "气泡里的话", "烦恼物件", "D", "办法物件", "一行注")          # 角色 + 物件
c3 = C_flow(左说明, 右说明, ["框", "框"], ["框", "框", "框"], rnote="一行注")                 # 流程框
sc = [scen("路径", 概率, 示意EPS, 低倍数, 高倍数, "green"), ...];  expect(sc);  scen_table(sc, 需要发生什么)
p = Page(..., notice=disclaimer("2026-11-11"))
```

积木画出来的图偏“标准件”；单份报告想画得更讲究，仍用 `Canvas` / `Comic` 手画，两者可以混用。

现成图表不够用时，直接用 `Canvas` 的基础图形自己画——工具箱是起点不是笼子；只要文字都走 `c.text()`，检查照样生效。

## 不能跑 Python 的时候

复制 `assets/template.html`，把 `{{BODY}}` 换成手写的 HTML + 内联 SVG，其余占位符(`{{TITLE}}` `{{LANG}}` `{{CAPMAX}}` `{{PAGE_KEY}}` `{{LABELS}}`)照 `sketch.py` 里 `Page.html()` 的值填。手写 SVG 必须遵守 `references/visual-style.md` 的画布坐标和 class 约定(`svg.chk`、`rect.panel`、`text.cap`)，内置自检才认得出来。在浏览器里打开 `页面.html?check=1`，底部检查条必须是绿色 PASS。

## 常见失败模式

- ❌ 概念按材料原顺序排 → 依赖链没有信息量，重排
- ❌ "代价是什么"写成"几乎没有代价" → 没想清楚，再想
- ❌ 不同概念的图里换了角色 → 读者要重新认人，统一
- ❌ 核心竞争力只有形容词（"品牌强大""技术领先"），没有数字和口径 → 换成证据
- ❌ 把管理层的愿景当成业绩指引写进远期规划 → 标清楚是目标，并和现在的速度对账
- ❌ 隐藏危机写成"宏观不确定性""竞争加剧"这种套话 → 写具体的传导路径和要盯的数
- ❌ 把没公告的日期写死 → 写"预计 12 月初（去年为 12/2，以公司公告为准）"
- ❌ 概率和价位不标"主观估计 / 示意" → 读者会当成预测
- ❌ 二手媒体说"没有新消息"就信了 → 先查公司公告和 SEC 文件
- ❌ 学习路线的链接没打开核实 → 最严重
- ❌ 正文写成长篇大论 → 每节 ≤ 4 句
- ❌ 没跑 `verify.py`、没看截图就交付 → 文字重叠的页面发出去了
