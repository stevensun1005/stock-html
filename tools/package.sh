#!/usr/bin/env bash
# Build dist/stock-html.zip — the skill folder on its own, ready to upload to claude.ai
# (Settings → Capabilities → Skills) or to unzip into ~/.claude/skills/.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist
( cd skills && zip -qr ../dist/stock-html.zip stock-html -x '*/__pycache__/*' -x '*.pyc' -x '*.DS_Store' )
echo "built dist/stock-html.zip ($(du -h dist/stock-html.zip | cut -f1))"
