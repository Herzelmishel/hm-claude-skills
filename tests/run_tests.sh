#!/usr/bin/env bash
# Run preseed-* test suite with branch coverage across all 5 skills
# (preseed-campaign, preseed-voice, preseed-prospect, preseed-outreach,
# preseed-pipeline). Exits non-zero if coverage falls below 85%.
#
# Subprocess coverage is enabled so tests that exec scripts via
# subprocess.run() also contribute to the coverage report.
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# --------------------------------------------------------------------------
# Subprocess coverage setup
# --------------------------------------------------------------------------
# We instruct the coverage library to start automatically in any subprocess
# that imports site (i.e. every standard CPython process) by:
#   1) writing a .coveragerc that enables parallel mode
#   2) exporting COVERAGE_PROCESS_START so coverage.process_startup() picks it up
#   3) installing a .pth file in the user's site-packages that calls
#      coverage.process_startup() before the subprocess's main code runs
cat > .coveragerc << 'EOF'
[run]
branch = True
parallel = True
source =
    ../preseed-campaign/scripts
    ../preseed-voice/scripts
    ../preseed-prospect/scripts
    ../preseed-outreach/scripts
    ../preseed-pipeline/scripts
EOF

export COVERAGE_PROCESS_START="$HERE/.coveragerc"

SITE_PATH="$(python3 -c 'import site; print(site.getusersitepackages())')"
mkdir -p "$SITE_PATH"
echo "import sys; exec('try:\\n  import coverage; coverage.process_startup()\\nexcept ImportError: pass')" > "$SITE_PATH/coverage_subprocess.pth"

# --------------------------------------------------------------------------
# Build absolute --include list covering all 14 instrumented scripts
# --------------------------------------------------------------------------
SOURCES=(
  "../preseed-campaign/scripts/build_campaign.py"
  "../preseed-campaign/scripts/momentum_check.py"
  "../preseed-campaign/scripts/validate_round_brief.py"
  "../preseed-voice/scripts/build_voice_fingerprint.py"
  "../preseed-voice/scripts/score_voice_match.py"
  "../preseed-prospect/scripts/score_investors.py"
  "../preseed-prospect/scripts/validate_investors_csv.py"
  "../preseed-outreach/scripts/count_message_chars.py"
  "../preseed-outreach/scripts/validate_outreach.py"
  "../preseed-pipeline/scripts/update_pipeline.py"
  "../preseed-pipeline/scripts/campaign_summary.py"
  "../preseed-pipeline/scripts/warm_list.py"
  "../preseed-pipeline/scripts/reapproach_notes.py"
  "../preseed-pipeline/scripts/ghost_check.py"
  "../preseed-pipeline/scripts/soft_circle_map.py"
)

INCLUDE=""
for src in "${SOURCES[@]}"; do
  abs="$(cd "$(dirname "$src")" && pwd)/$(basename "$src")"
  if [ -z "$INCLUDE" ]; then
    INCLUDE="$abs"
  else
    INCLUDE="$INCLUDE,$abs"
  fi
done

# --------------------------------------------------------------------------
# Run pytest under coverage; combine in-process + subprocess data files.
# --------------------------------------------------------------------------
# Clean any stale coverage data files from previous runs.
python3 -m coverage erase

python3 -m coverage run --branch --parallel-mode --include="$INCLUDE" \
  -m pytest \
  preseed_campaign \
  preseed_voice \
  preseed_prospect \
  preseed_outreach \
  preseed_pipeline

# Combine the per-process .coverage.* files (subprocess + main) into one.
python3 -m coverage combine

# 85% safety floor — temporary while subprocess coverage stabilises.
python3 -m coverage report --skip-empty --include="$INCLUDE" --fail-under=85
python3 -m coverage html -d _coverage_html --include="$INCLUDE"
echo "HTML coverage report: $HERE/_coverage_html/index.html"
