# preseed-* script tests

Unit tests for the Python scripts that power the `/preseed-*` skill suite.

## What's covered

| Script | Test file | Notes |
|---|---|---|
| `preseed-campaign/scripts/build_campaign.py` | `preseed_campaign/test_build_campaign.py` | workspace bootstrap, force overwrite, anti-voice extraction, error envelope |
| `preseed-campaign/scripts/validate_round_brief.py` | `preseed_campaign/test_validate_round_brief.py` | required-field checks, vague-claim detection, block scalar parsing (regression), PyYAML + stdlib fallback |
| `preseed-campaign/scripts/momentum_check.py` | `preseed_campaign/test_momentum_check.py` | momentum_score formula, velocity status, time-to-close math, campaign.yaml in-place upsert |
| `preseed-voice/scripts/build_voice_fingerprint.py` | `preseed_voice/test_build_voice_fingerprint.py` | feature extraction, register classification, anti-voice append |
| `preseed-voice/scripts/score_voice_match.py` | `preseed_voice/test_score_voice_match.py` | banned-phrase veto cap, sentence/opener/em-dash sub-scores, stdin handling |

## Running

From this directory:

```bash
./run_tests.sh
```

The script:

1. Runs `pytest` under `coverage run --branch` with `--include` limited to the
   five instrumented scripts so unrelated stdlib hits don't dilute the report.
2. Prints a coverage report and **fails the run** if coverage drops below 90%.
3. Writes an HTML report to `_coverage_html/index.html`.

To run a single test file:

```bash
python3 -m pytest preseed_campaign/test_validate_round_brief.py -v
```

## Adding tests for new scripts

1. Add a new `test_<script_name>.py` under either `preseed_campaign/` or
   `preseed_voice/` (mirror the source layout).
2. If the script needs a workspace, use the `tmp_workspace` fixture from
   `conftest.py` — it monkey-patches `Path.home()` and seeds a complete
   `~/fundraising/` tree.
3. Append the new script's absolute path to `SOURCES` in `run_tests.sh` so
   it gets included in the coverage gate.
4. Aim for line + branch coverage ≥ 95% on new scripts.

## Notes on the YAML test seam

PyYAML is optional for the scripts under test — they fall back to a stdlib
YAML mini-parser when `import yaml` fails. The validate-round-brief tests
parametrize over both code paths via a `monkeypatch`-driven import block
to ensure both branches are exercised.

## Why monkey-patch `Path.home()` instead of `HOME`

The campaign / voice scripts call `Path.home()` directly. `pathlib.Path.home`
on macOS/Linux falls back to `pwd.getpwuid` if `HOME` is unset, so just
setting `HOME` isn't always sufficient. Patching `Path.home` is the
hermetic option.
