# Changelog

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
