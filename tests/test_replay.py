"""Replay a committed redacted fake-adapter trace."""

from __future__ import annotations

import json
from pathlib import Path

TRACE = Path(__file__).parent / "fixtures" / "traces" / "fake-canary.jsonl"


def test_replay_redacted_fake_trace() -> None:
    types: list[str] = []
    for line in TRACE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        blob = json.dumps(event)
        assert "sk-" not in blob
        assert "BEGIN" not in blob
        types.append(str(event.get("type")))
    assert "system" in types
    assert "result" in types
