from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


StepState = Literal[
    "pending",
    "running",
    "completed",
    "partial",
    "failed",
    "skipped",
    "needs_user_input",
]

ArtifactKind = Literal[
    "metadata",
    "pdf",
    "tex_source",
    "figure",
    "note",
    "terminology",
    "doubts",
    "code_reference",
    "interview_mapping",
    "job_record",
]


@dataclass
class AgentStep:
    id: str
    name: str
    state: StepState = "pending"
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    started_at: str | None = None
    ended_at: str | None = None
    error: str | None = None


@dataclass
class Artifact:
    kind: ArtifactKind
    path: str
    label: str


@dataclass
class PaperMetadata:
    slug: str
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    abstract: str | None
    canonical_url: str | None
    pdf_url: str | None
    source_url: str | None
    github_candidates: list[str]
    created_at: str
    status: Literal["intake_completed", "intake_partial"]


@dataclass
class ResearchJob:
    id: str
    input_text: str
    status: StepState
    paper_slug: str | None
    created_at: str
    updated_at: str
    metadata: PaperMetadata | None
    steps: list[AgentStep]
    artifacts: list[Artifact]


def to_dict(value):
    return asdict(value)

