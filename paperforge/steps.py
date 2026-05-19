from __future__ import annotations

from datetime import UTC, datetime

from paperforge.models import AgentStep, StepState


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def create_step(step_id: str, name: str, inputs: list[str]) -> AgentStep:
    return AgentStep(id=step_id, name=name, inputs=inputs)


def start_step(step: AgentStep) -> AgentStep:
    step.state = "running"
    step.started_at = now_iso()
    return step


def finish_step(
    step: AgentStep,
    state: StepState,
    outputs: list[str],
    error: str | None = None,
) -> AgentStep:
    step.state = state
    step.outputs = outputs
    step.error = error
    step.ended_at = now_iso()
    return step

