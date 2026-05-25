from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from paperforge.ai_paper_reader_prompt import CANONICAL_SKILL_PATH, PROJECT_SKILL_PATH
from paperforge.llm_client import ChatClient, LlmConfigError, reader_chat_client_from_env
from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_paper_vault_dir, get_project_root, relative_to_data_dir, save_job


MAX_SKILL_CHARS = 16000
MAX_METADATA_CHARS = 4000
MAX_NOTE_CHARS = 12000
MAX_EVIDENCE_CHARS = 24000
MAX_EVIDENCE_CHUNKS_CHARS = 24000
MAX_MANIFEST_CHARS = 8000


@dataclass(frozen=True)
class ReaderArtifactStatus:
    relative_path: str
    absolute_path: Path
    present: bool
    max_chars: int


def run_ai_paper_reader_note_generation(
    job: ResearchJob,
    *,
    client: ChatClient | None = None,
    model: str | None = None,
) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("AI paper reader note generation requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_path = notes_dir / "ai-paper-reader-note.md"
    prompt_path = notes_dir / "ai-paper-reader-generation-prompt.md"

    step = start_step(
        create_step(
            "note.generate_ai_paper_reader_note",
            "Generate ai-paper-reader note",
            [
                "docs/PAPER_SKILL.md",
                "metadata.json",
                "raw/paper.pdf",
                "notes/README.md",
                "notes/evidence-chunks.md",
                "notes/evidence-map.md",
                "images/manifest.md",
            ],
        )
    )
    job.steps.append(step)

    if client is None or model is None:
        try:
            client, model = reader_chat_client_from_env()
        except LlmConfigError as error:
            finish_step(step, "needs_user_input", [], str(error))
            job.status = "needs_user_input"
            job.updated_at = now_iso()
            save_job(job)
            return job

    statuses = _artifact_statuses(paper_dir)
    prompt = _reader_prompt(job, paper_dir, statuses)
    prompt_path.write_text(prompt, encoding="utf-8")

    try:
        generated_note = client.chat(_messages(prompt), model=model, temperature=0.2)
        note_path.write_text(generated_note, encoding="utf-8")
    except Exception as error:
        finish_step(step, "failed", [relative_to_data_dir(prompt_path)], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, note_path, "AI Paper Reader Note")
    _add_artifact(job, prompt_path, "AI Paper Reader Generation Prompt")
    outputs = [relative_to_data_dir(note_path), relative_to_data_dir(prompt_path)]

    if any(not status.present for status in statuses):
        finish_step(step, "partial", outputs, "Some recommended artifacts are missing")
        job.status = "partial"
    else:
        finish_step(step, "completed", outputs)

    job.updated_at = now_iso()
    save_job(job)
    return job


def _messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an expert AI paper reader. Follow the provided skill and evidence rules. "
                "Return only the final Markdown reading note."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]


def _artifact_statuses(paper_dir: Path) -> list[ReaderArtifactStatus]:
    evidence_status = _primary_evidence_status(paper_dir)
    return [
        ReaderArtifactStatus("metadata.json", paper_dir / "metadata.json", (paper_dir / "metadata.json").exists(), MAX_METADATA_CHARS),
        ReaderArtifactStatus("raw/paper.pdf", paper_dir / "raw" / "paper.pdf", (paper_dir / "raw" / "paper.pdf").exists(), 0),
        ReaderArtifactStatus("notes/README.md", paper_dir / "notes" / "README.md", (paper_dir / "notes" / "README.md").exists(), MAX_NOTE_CHARS),
        evidence_status,
        ReaderArtifactStatus(
            "images/manifest.md",
            paper_dir / "images" / "manifest.md",
            (paper_dir / "images" / "manifest.md").exists(),
            MAX_MANIFEST_CHARS,
        ),
    ]


def _primary_evidence_status(paper_dir: Path) -> ReaderArtifactStatus:
    chunks_path = paper_dir / "notes" / "evidence-chunks.md"
    if chunks_path.exists():
        return ReaderArtifactStatus("notes/evidence-chunks.md", chunks_path, True, MAX_EVIDENCE_CHUNKS_CHARS)

    evidence_map_path = paper_dir / "notes" / "evidence-map.md"
    return ReaderArtifactStatus(
        "notes/evidence-map.md",
        evidence_map_path,
        evidence_map_path.exists(),
        MAX_EVIDENCE_CHARS,
    )


def _reader_prompt(job: ResearchJob, paper_dir: Path, statuses: list[ReaderArtifactStatus]) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("AI paper reader note generation requires paper metadata")

    skill_path = get_project_root() / "docs" / "PAPER_SKILL.md"
    skill_content = _read_text_excerpt(skill_path, MAX_SKILL_CHARS)
    lines = [
        "# Generate AI Paper Reader Note",
        "",
        "Use the skill content and PaperForge artifacts below to generate a professional paper reading note.",
        "",
        "## Skill",
        "",
        f"- Project skill path: {PROJECT_SKILL_PATH}",
        f"- Project skill absolute path: {skill_path}",
        f"- Canonical installed skill path: {CANONICAL_SKILL_PATH}",
        "",
        "```markdown",
        skill_content,
        "```",
        "",
        "## Paper",
        "",
        f"- Workspace: {paper_dir}",
        f"- Title: {metadata.title}",
        f"- Authors: {', '.join(metadata.authors) if metadata.authors else 'Unknown'}",
        f"- Year: {metadata.year if metadata.year is not None else 'Unknown'}",
        f"- Canonical URL: {metadata.canonical_url or 'not resolved'}",
        "",
        "## Artifact Inventory",
        "",
        *_artifact_table_lines(statuses),
        "## Artifact Excerpts",
        "",
        *_artifact_excerpt_lines(statuses),
        "## Output Requirements",
        "",
        "- Use this structure: metadata, TL;DR, paper overview, background and motivation, core method, experiments, deep Q&A, summary and reflections.",
        "- Do not invent paper content. If a claim cannot be verified from the listed artifacts, mark it as needs verification.",
        "- Missing artifacts must be treated as unavailable, not guessed from memory.",
        "- Prefer notes/evidence-chunks.md for paper facts when present because chunk ids provide the most precise evidence.",
        "- If notes/evidence-chunks.md is unavailable, fall back to notes/evidence-map.md page evidence.",
        "- Prioritize chunk id citations such as `p001-c001`; if only page evidence is available, cite the page.",
        "- If a claim cannot be verified from a chunk, mark it as needs verification and do not fill paper details from model memory.",
        "- Use images/manifest.md only for figure references that are present in the manifest.",
        "- Return final Markdown only.",
        "",
    ]
    return "\n".join(lines)


def _artifact_table_lines(statuses: list[ReaderArtifactStatus]) -> list[str]:
    lines = [
        "| Artifact | Status | Absolute path |",
        "| --- | --- | --- |",
    ]
    for status in statuses:
        marker = "present" if status.present else "missing"
        lines.append(f"| {status.relative_path} | {marker} | `{status.absolute_path}` |")
    lines.append("")
    return lines


def _artifact_excerpt_lines(statuses: list[ReaderArtifactStatus]) -> list[str]:
    lines: list[str] = []
    for status in statuses:
        lines.extend([f"### {status.relative_path}", ""])
        if not status.present:
            lines.extend(["Missing.", ""])
            continue
        if status.max_chars <= 0:
            lines.extend(["Binary or non-text artifact. Use the path only; do not assume unread content.", ""])
            continue
        lines.extend(["```text", _read_text_excerpt(status.absolute_path, status.max_chars), "```", ""])
    return lines


def _read_text_excerpt(path: Path, max_chars: int) -> str:
    if not path.exists():
        return "Missing."
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[truncated]"


def _add_artifact(job: ResearchJob, path: Path, label: str) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "note"
            artifact.label = label
            return
    job.artifacts.append(Artifact("note", artifact_path, label))
