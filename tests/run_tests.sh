#!/usr/bin/env bash
# Run preseed-* test suite with branch coverage. Exits non-zero if
# coverage of the 5 instrumented scripts falls below 90%.
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

SOURCES=(
  "../preseed-campaign/scripts/build_campaign.py"
  "../preseed-campaign/scripts/validate_round_brief.py"
  "../preseed-campaign/scripts/momentum_check.py"
  "../preseed-voice/scripts/build_voice_fingerprint.py"
  "../preseed-voice/scripts/score_voice_match.py"
)

# Build a comma-separated --include list (resolved to absolute paths).
INCLUDE=""
for src in "${SOURCES[@]}"; do
  abs="$(cd "$(dirname "$src")" && pwd)/$(basename "$src")"
  if [ -z "$INCLUDE" ]; then
    INCLUDE="$abs"
  else
    INCLUDE="$INCLUDE,$abs"
  fi
done

python3 -m coverage run --branch --include="$INCLUDE" -m pytest preseed_campaign preseed_voice
python3 -m coverage report --skip-empty --fail-under=90
python3 -m coverage html -d _coverage_html
echo "HTML coverage report: $HERE/_coverage_html/index.html"
