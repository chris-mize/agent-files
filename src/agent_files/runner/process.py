"""Process-group spawn with timeout and killpg."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from agent_files.models.run import CompletedRun
from agent_files.redact import redact


def spawn_process(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    stdin: int = subprocess.DEVNULL,
    trace_path: Path | None = None,
) -> CompletedRun:
    started = time.monotonic()
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        text=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = proc.communicate()
    duration_ms = int((time.monotonic() - started) * 1000)
    stdout = redact(stdout or "")
    stderr = redact(stderr or "")
    if trace_path is not None:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(stdout, encoding="utf-8")
    return CompletedRun(
        workspace=cwd,
        returncode=proc.returncode if proc.returncode is not None else -9,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        duration_ms=duration_ms,
        trace_path=trace_path,
        argv=argv,
    )


def allowed_env(allowlist: list[str], extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {key: os.environ[key] for key in allowlist if key in os.environ}
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = env.get("PYTHONPATH", "")
    if extra:
        env.update(extra)
    # Ensure the current interpreter remains runnable for the fake adapter.
    path = env.get("PATH", "")
    bindir = str(Path(sys.executable).parent)
    if bindir not in path.split(os.pathsep):
        env["PATH"] = os.pathsep.join([bindir, path]) if path else bindir
    return env
