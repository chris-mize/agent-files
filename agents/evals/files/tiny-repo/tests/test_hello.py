from pathlib import Path


def test_hello() -> None:
    assert Path("hello.txt").read_text(encoding="utf-8") == "ok\n"
