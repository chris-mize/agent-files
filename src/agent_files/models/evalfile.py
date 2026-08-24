"""evals.json contracts."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvalState(StrEnum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REPRODUCED = "reproduced"
    FROZEN = "frozen"
    RELEASED = "released"


class EvalSource(BaseModel):
    state: EvalState
    issue: str | None = None
    prompt_hash: str
    prompt_file: str | None = None
    approved_by: str | None = None
    review_path: str | None = None
    known_gap: bool = False


class GraderSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str

    def options(self) -> dict[str, Any]:
        data = self.model_dump()
        data.pop("type")
        return data


class EvalItem(BaseModel):
    id: int
    prompt: str = ""
    expected_output: str = ""
    files: list[str] = Field(default_factory=list)
    expectations: list[str] = Field(default_factory=list)
    assertions: list[str] = Field(default_factory=list)
    graders: list[GraderSpec] = Field(default_factory=list)
    crowded: bool = False
    source: EvalSource

    @property
    def all_expectations(self) -> list[str]:
        return [*self.expectations, *self.assertions]

    @model_validator(mode="after")
    def frozen_requires_graders(self) -> Self:
        if (
            self.source.state in {EvalState.FROZEN, EvalState.RELEASED}
            and not self.graders
        ):
            raise ValueError("frozen and released evals require graders")
        return self


class EvalsFile(BaseModel):
    schema_version: Literal[1] = 1
    skill_name: str
    evals: list[EvalItem]

    def get(self, eval_id: int) -> EvalItem:
        for item in self.evals:
            if item.id == eval_id:
                return item
        raise KeyError(eval_id)


def load_evals_file(path: Path) -> EvalsFile:
    return EvalsFile.model_validate_json(path.read_text(encoding="utf-8"))


def write_evals_file(path: Path, data: EvalsFile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        data.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )


# Names used by graders / CLI.
EvalItem = EvalItem
EvalState = EvalState
EvalSource = EvalSource
GraderSpec = GraderSpec
EvalsFile = EvalsFile
load_evals_file = load_evals_file
write_evals_file = write_evals_file
