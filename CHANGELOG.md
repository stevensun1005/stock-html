# Changelog

## 1.2.0

- `blocks.org_change()`: before/after diagram for leadership or structure changes, with the departed role drawn as a red dashed box.
- `waterfall()`: long step labels split onto two lines when there are many steps, so neighbouring labels no longer run together.
- `references/stock-report.md`: new section "重大事件后的更新" — how to update an existing report after a major event (sources, notice, an event section with a before/after table and market reaction, and which default sections must change).

## 1.1.0

- New `scripts/blocks.py`: ready-made building blocks on top of `sketch.py` — `mainline_tug` (business vs. share price), `moat`, `vision` (three bars with a red gap), three two-panel comic layouts (`C_bars`, `C_talk`, `C_flow`), scenario helpers (`scen`, `expect`, `scen_table`) and `disclaimer()`. Built for producing many reports in one go (e.g. an ETF's top ten holdings); all text still goes through `Canvas.text()`, so both layout checks still apply.
- Layout fixes baked into the blocks: the vision chart reserves room for its footnote, bar-comic value labels no longer collide with the panel note, and the mainline price line keeps its first label off the line.

## 1.0.2

- `scripts/sketch.py`: `roadmap()` is 16px taller, so the lowest step fits three bullet points without the last one touching the box edge.

## 1.0.1

- `scripts/verify.py`: fixed two Windows issues — Chrome's UTF-8 output no longer crashes on systems whose default code page is GBK, and `--shots` now works with relative paths (screenshots were silently not saved).

## 1.0.0

First public release.

- Stock reports now include, by default: health check, core moat, tech roadmap, long-term plan, hidden risks, key dates, price scenarios and the valuation ruler. The build warns when one is missing.
- `scripts/sketch.py`: a standard-library toolkit for hand-drawn SVG — canvas primitives, fixed-cast characters, two-panel comics, and ready-made charts (`snake`, `timeline`, `roadmap`, `risk_matrix`, `paths_chart`, `ruler_chart`, `waterfall`, `metro`).
- Offline pre-check on `Page.save()`: text overflow, overlap, comic-panel containment, caption length, prose length, empty "cost" lines, unverified links, broken concept chains.
- `scripts/verify.py`: real render in headless Chrome / Chromium / Edge, both themes, with sliced or per-section screenshots.
- `assets/template.html`: graph-paper and chalkboard themes, wobble filter, clickable progress stamps, built-in layout self-check (`?check=1`).
- Chinese and English page labels (`set_lang`).
- Worked example with a fictional company: `examples/boba_merger.py`.
- Installable as a Claude Code plugin, as a personal skill, or as a zip upload on claude.ai.
