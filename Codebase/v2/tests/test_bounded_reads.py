"""Bounded-read tests: giant JSONL histories do not load unbounded."""
import json

from Codebase.v2.config import MAX_JSON_LINE_CHARS, MAX_METADATA_SCAN_BYTES
from Codebase.v2.providers.base import iter_jsonl_records


def test_oversized_lines_are_skipped(tmp_path):
    fp = tmp_path / "big.jsonl"
    huge = "x" * (MAX_JSON_LINE_CHARS + 50)
    fp.write_text(
        json.dumps({"keep": 1}) + "\n" + huge + "\n" + json.dumps({"keep": 2}) + "\n",
        encoding="utf-8",
    )
    records = list(iter_jsonl_records(fp))
    assert records == [{"keep": 1}, {"keep": 2}]


def test_max_bytes_budget_stops_early(tmp_path):
    fp = tmp_path / "many.jsonl"
    line = json.dumps({"n": 1}) + "\n"
    # ~10 bytes/line -> 400 lines ~ 4KB, well under default 2MB metadata cap,
    # but we pass an explicit small budget to prove it stops.
    fp.write_text(line * 400, encoding="utf-8")
    records = list(iter_jsonl_records(fp, max_bytes=200))
    assert len(records) < 400
    assert len(records) > 0


def test_default_metadata_cap_is_two_mib():
    assert MAX_METADATA_SCAN_BYTES == 2 * 1024 * 1024