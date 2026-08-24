"""Review JSON contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Verdict = Literal["ready", "ready with changes", "not ready"]


class ReviewFinding(BaseModel):
    summary: str
    severity: str = "medium"


class ReviewDocument(BaseModel):
    verdict: Verdict
    findings: list[ReviewFinding] = Field(default_factory=list)
    gate: str
    artifact: str
    eval_id: int | None = None
