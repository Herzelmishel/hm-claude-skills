"""Tests for preseed-campaign/scripts/validate_round_brief.py."""

from __future__ import annotations

import builtins
import json
import sys

import pytest


def _import():
    if "validate_round_brief" in sys.modules:
        del sys.modules["validate_round_brief"]
    import validate_round_brief
    return validate_round_brief


# ---------------------------------------------------------------------------
# Parametrize across PyYAML and stdlib parser
# ---------------------------------------------------------------------------

@pytest.fixture(params=["pyyaml", "stdlib"])
def parser_mode(request, monkeypatch):
    """Either let PyYAML be importable, or simulate it not being installed."""
    if request.param == "stdlib":
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("simulated: pyyaml unavailable")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", fake_import)
    return request.param


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_brief_when_all_fields_present_then_exit_0(
        tmp_workspace, parser_mode, capsys):
    vrb = _import()
    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert "fields_validated" in payload
    assert "vague_claim_warnings" in payload


# ---------------------------------------------------------------------------
# Required-field handling
# ---------------------------------------------------------------------------

def test_missing_field_returns_envelope_with_field_set(
        tmp_workspace, seed_round_brief, parser_mode, capsys):
    vrb = _import()
    seed_round_brief(
        tmp_workspace,
        content="one_liner: a one-liner here\n",  # only one field
    )
    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "Missing required field" in payload["error"]
    assert payload["field"]  # one of the missing fields


def test_empty_field_returns_envelope_with_field_set(
        tmp_workspace, seed_round_brief, parser_mode, capsys):
    vrb = _import()
    seed_round_brief(tmp_workspace, overrides={"problem": ""})
    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "empty" in payload["error"]


# ---------------------------------------------------------------------------
# Vague-claim detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "vague_phrase",
    [
        "we have significant traction",
        "world-class team executing fast",
        "best-in-class profit floor",
        "this is a game-changer for ecommerce",
        "massive market opportunity",
        "we will revolutionize ecommerce",
        "our unique value proposition",
        "powerful synergy across teams",
        "disruptive go-to-market",
        "next-generation profit suite",
        "strong traction this quarter",
        "huge tam in our segment",
        "ground-breaking results so far",
    ],
)
def test_vague_claim_detected(
        tmp_workspace, seed_round_brief, parser_mode, capsys, vague_phrase):
    vrb = _import()
    seed_round_brief(
        tmp_workspace,
        overrides={"traction": [f"2 paid pilots; {vague_phrase}"]},
    )
    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["vague_claim_warnings"], (
        f"expected '{vague_phrase}' to trigger a warning"
    )
    assert payload["warning_message"]


# ---------------------------------------------------------------------------
# Block scalar parsing — REGRESSION
# ---------------------------------------------------------------------------

def test_block_scalar_pipe_does_not_bleed_into_next_key(
        tmp_workspace, parser_mode, capsys):
    """Regression: literal block scalar content must not pollute the next key."""
    vrb = _import()
    text = (
        "one_liner: |\n"
        "  multi\n"
        "  line\n"
        "  content here\n"
        "problem: short problem statement\n"
        "why_now: now\n"
        "solution: solve\n"
        "traction:\n"
        "  - 2 pilots\n"
        "ask: 1M SAFE\n"
        "team:\n"
        "  - Herzel\n"
        "ideal_investor:\n"
        "  - operator angels\n"
        "exclusions:\n"
        "  - retail-only\n"
        "risks:\n"
        "  - integration\n"
    )
    (tmp_workspace / "story" / "round-brief.yaml").write_text(text, encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 0


def test_folded_scalar_parses(tmp_workspace, parser_mode, capsys):
    vrb = _import()
    text = (
        "one_liner: >\n"
        "  folded\n"
        "  content here\n"
        "problem: p\n"
        "why_now: w\n"
        "solution: s\n"
        "traction:\n"
        "  - 1 pilot\n"
        "ask: 1M\n"
        "team:\n"
        "  - me\n"
        "ideal_investor:\n"
        "  - angels\n"
        "exclusions:\n"
        "  - retail\n"
        "risks:\n"
        "  - r\n"
    )
    (tmp_workspace / "story" / "round-brief.yaml").write_text(text, encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 0


def test_block_scalar_followed_by_another_key_does_not_swallow_it(
        tmp_workspace, parser_mode, capsys):
    vrb = _import()
    text = (
        "one_liner: |\n"
        "  Agentis stops margin leaks for mid-market Shopify brands.\n"
        "problem: |\n"
        "  Mid-market Shopify brands lose margin every month.\n"
        "  Pricing errors and promo overlap are common drivers.\n"
        "why_now: shopify functions just shipped\n"
        "solution: real-time profit floor\n"
        "traction:\n"
        "  - 2 paid pilots\n"
        "ask: 1M SAFE\n"
        "team:\n"
        "  - Herzel\n"
        "ideal_investor:\n"
        "  - operator angels\n"
        "exclusions:\n"
        "  - retail-only\n"
        "risks:\n"
        "  - r\n"
    )
    (tmp_workspace / "story" / "round-brief.yaml").write_text(text, encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 0


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_yaml_parse_error_returns_envelope(tmp_workspace, parser_mode, capsys):
    vrb = _import()
    # Garbage that PyYAML rejects — and our minimal parser also can't make sense of.
    # The real scripts wrap any exception, so we trigger one via the
    # _load_yaml stub.
    (tmp_workspace / "story" / "round-brief.yaml").write_text(
        "\t\t\t\nnot: : valid\n", encoding="utf-8",
    )
    # Force an explicit parse error by monkeypatching the loader.
    import sys as _s
    mod = _s.modules["validate_round_brief"]
    mod._load_yaml = lambda text: (_ for _ in ()).throw(ValueError("bad yaml"))
    with pytest.raises(SystemExit) as exc:
        mod.main([])
    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "YAML parse failed" in payload["error"]


def test_missing_file_returns_exit_2_with_envelope(empty_home, parser_mode, capsys):
    vrb = _import()
    # No fundraising tree exists.
    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "round-brief.yaml not found" in payload["error"]
    assert "fix" in payload


def test_empty_yaml_file_returns_envelope(tmp_workspace, parser_mode, capsys):
    vrb = _import()
    (tmp_workspace / "story" / "round-brief.yaml").write_text("\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        vrb.main([])
    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "empty" in payload["error"] or "Missing required field" in payload["error"]


def test_path_flag_overrides_default(tmp_workspace, parser_mode, capsys, tmp_path):
    vrb = _import()
    custom = tmp_path / "custom-brief.yaml"
    custom.write_text(
        (tmp_workspace / "story" / "round-brief.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc:
        vrb.main(["--path", str(custom)])
    assert exc.value.code == 0


# ---------------------------------------------------------------------------
# Tiny-loader unit tests (only exercised in stdlib mode, but they call
# the helpers directly so they always run)
# ---------------------------------------------------------------------------

def test_minimal_loader_handles_lists_and_quoted_scalars():
    vrb = _import()
    text = (
        'name: "Quoted Value"\n'
        "items:\n"
        "  - one\n"
        "  - two\n"
        "  - 'three'\n"
        "count: 5\n"
        "ratio: 0.5\n"
        "active: true\n"
        "missing: null\n"
    )
    out = vrb._load_yaml_minimal(text)
    assert out["name"] == "Quoted Value"
    assert out["items"] == ["one", "two", "three"]
    assert out["count"] == 5
    assert out["ratio"] == 0.5
    assert out["active"] is True
    assert out["missing"] is None


def test_minimal_loader_handles_nested_map():
    vrb = _import()
    text = (
        "ask:\n"
        "  raise_usd: 1000000\n"
        "  instrument: SAFE\n"
    )
    out = vrb._load_yaml_minimal(text)
    assert out["ask"]["raise_usd"] == 1000000
    assert out["ask"]["instrument"] == "SAFE"


def test_minimal_loader_handles_chomping_indicator():
    vrb = _import()
    text = (
        "key: |-\n"
        "  line1\n"
        "  line2\n"
        "next: x\n"
    )
    out = vrb._load_yaml_minimal(text)
    assert out["key"].startswith("line1")
    assert "line2" in out["key"]
    # |- means strip trailing newline
    assert not out["key"].endswith("\n")
    assert out["next"] == "x"


def test_is_empty_helper():
    vrb = _import()
    assert vrb._is_empty(None)
    assert vrb._is_empty("")
    assert vrb._is_empty("   ")
    assert vrb._is_empty([])
    assert vrb._is_empty({})
    assert not vrb._is_empty("x")
    assert not vrb._is_empty([1])
    assert not vrb._is_empty(0)


def test_flatten_for_search_handles_all_types():
    vrb = _import()
    assert vrb._flatten_for_search(None) == ""
    assert vrb._flatten_for_search("hi") == "hi"
    assert "a" in vrb._flatten_for_search(["a", "b"])
    assert "v" in vrb._flatten_for_search({"k": "v"})
    assert vrb._flatten_for_search(42) == "42"


def test_inline_comment_stripping_preserves_quoted_hash():
    vrb = _import()
    text = 'key: "has # hash inside"  # outside comment\n'
    out = vrb._load_yaml_minimal(text)
    assert out["key"] == "has # hash inside"
