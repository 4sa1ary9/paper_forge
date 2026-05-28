from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import streamlit as st

from paperforge.ai_paper_reader_prompt import run_ai_paper_reader_prompt_pack
from paperforge.ai_paper_reader_note import run_ai_paper_reader_note_generation
from paperforge.asset_collector import run_asset_collection
from paperforge.batch_runner import run_batch_intake
from paperforge.code_linker import run_code_linking, run_code_mapping_evidence
from paperforge.deep_note_planner import run_deep_note_planning
from paperforge.deep_note_writer import run_deep_note_writing
from paperforge.doubts_agent import run_doubts_evidence, run_doubts_scaffold
from paperforge.interview_mapper import run_interview_mapping_assessment, run_interview_mapping_scaffold
from paperforge.intake_agent import run_paper_intake
from paperforge.note_writer import run_note_writing
from paperforge.package_validator import run_package_validation
from paperforge.evidence_chunker import run_evidence_chunk_extraction
from paperforge.evidence_retriever import run_evidence_search
from paperforge.pdf_image_extractor import run_pdf_image_extraction
from paperforge.pdf_text_extractor import run_pdf_text_extraction
from paperforge.source_enrichment import run_source_enrichment
from paperforge.storage import get_data_dir, list_jobs
from paperforge.terminology_agent import run_terminology_evidence, run_terminology_scaffold
from paperforge.models import ResearchJob


st.set_page_config(page_title="PaperForge Agent", page_icon="PF", layout="wide")


# ── Phase definitions ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ActionStep:
    key: str
    label: str
    icon: str
    fn: Callable
    requires_metadata: bool = True
    phase: int = 1


ACTIONS: list[ActionStep] = [
    # Phase 1 — Intake
    ActionStep("intake", "Start Intake", "1", run_paper_intake, requires_metadata=False, phase=1),
    # Phase 2 — Assets
    ActionStep("collect_assets", "Collect Assets (PDF + TeX)", "2", run_asset_collection, phase=2),
    ActionStep("extract_images", "Extract PDF Images", "3", run_pdf_image_extraction, phase=2),
    ActionStep("enrich_sources", "Enrich External Sources", "4", run_source_enrichment, phase=2),
    ActionStep("link_code", "Link Code Candidates", "5", run_code_linking, phase=2),
    # Phase 3 — Scaffolds
    ActionStep("write_note", "Write Note Scaffold", "6", run_note_writing, phase=3),
    ActionStep("write_terminology", "Write Terminology Scaffold", "7", run_terminology_scaffold, phase=3),
    ActionStep("write_doubts", "Write Doubts Scaffold", "8", run_doubts_scaffold, phase=3),
    ActionStep("write_interview", "Write Interview Mapping Scaffold", "9", run_interview_mapping_scaffold, phase=3),
    # Phase 4 — Evidence
    ActionStep("extract_text", "Extract PDF Text Evidence", "10", run_pdf_text_extraction, phase=4),
    ActionStep("extract_chunks", "Extract Evidence Chunks", "11", run_evidence_chunk_extraction, phase=4),
    ActionStep("search_evidence", "Search Evidence Chunks", "12", run_evidence_search, phase=4),
    ActionStep("validate_package", "Validate Research Package", "13", run_package_validation, phase=4),
    # Phase 5 — Deep Generation
    ActionStep("plan_deep_note", "Plan Deep Note Readiness", "14", run_deep_note_planning, phase=5),
    ActionStep("write_deep_note", "Write Deep Note MVP", "15", run_deep_note_writing, phase=5),
    ActionStep("prepare_reader_prompt", "Prepare ai-paper-reader Prompt", "16", run_ai_paper_reader_prompt_pack, phase=5),
    ActionStep("generate_reader_note", "Generate ai-paper-reader Note", "17", run_ai_paper_reader_note_generation, phase=5),
    ActionStep("write_terminology_evidence", "Write Terminology Evidence", "18", run_terminology_evidence, phase=5),
    ActionStep("write_doubts_evidence", "Write Doubts Evidence", "19", run_doubts_evidence, phase=5),
    ActionStep("write_code_mapping", "Write Code Mapping Evidence", "20", run_code_mapping_evidence, phase=5),
    ActionStep("assess_interview", "Assess Interview Project", "21", run_interview_mapping_assessment, phase=5),
]

PHASES = {
    1: ("Phase 1: Intake", "Resolve paper identity and create research workspace"),
    2: ("Phase 2: Assets", "Download PDF, extract images, enrich sources, link code"),
    3: ("Phase 3: Scaffolds", "Generate skeleton documents for notes, terminology, doubts"),
    4: ("Phase 4: Evidence", "Extract text evidence, build chunks, validate research package"),
    5: ("Phase 5: Deep Generation", "Generate evidence-backed deep notes and assessments"),
}


# ── Session state init ──────────────────────────────────────────────────────

def init_session():
    defaults = {
        "active_job_id": None,
        "active_phase": 1,
        "source_urls": "",
        "local_code_repo": "",
        "evidence_query": "",
        "auto_run": False,
        "completed_steps": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Helpers ──────────────────────────────────────────────────────────────────

def step_state(job: ResearchJob, step_key: str) -> str:
    """Derive step state from job step history."""
    step_name_map = {
        "intake": "Resolve paper identity",
        "collect_assets": "Download PDF",
        "extract_images": "Extract PDF images",
        "enrich_sources": "Enrich external sources",
        "link_code": "Link code repositories",
        "write_note": "Write paper note scaffold",
        "write_terminology": "Write terminology scaffold",
        "write_doubts": "Write doubts scaffold",
        "write_interview": "Write interview project mapping scaffold",
        "extract_text": "Extract PDF text evidence",
        "extract_chunks": "Extract evidence chunks",
        "search_evidence": "Search evidence chunks",
        "validate_package": "Validate research package",
        "plan_deep_note": "Plan deep note readiness",
        "write_deep_note": "Write deep note MVP",
        "prepare_reader_prompt": "Prepare ai-paper-reader prompt",
        "generate_reader_note": "Generate ai-paper-reader note",
        "write_terminology_evidence": "Write terminology evidence draft",
        "write_doubts_evidence": "Write doubts evidence draft",
        "write_code_mapping": "Map paper method evidence to code paths",
        "assess_interview": "Assess interview project suitability",
    }
    name = step_name_map.get(step_key, step_key)
    for s in job.steps:
        if s.name == name:
            return s.state
    return "pending"


def is_step_available(job: ResearchJob, action: ActionStep) -> bool:
    """Check if a step can be run now."""
    if action.requires_metadata and job.metadata is None:
        return False
    # Each phase needs the first step of the previous phase to be completed
    phase_prereqs = {
        2: "intake",
        3: "write_note",  # can start after note scaffold
        4: "collect_assets",
        5: "extract_text",
    }
    prereq = phase_prereqs.get(action.phase)
    if prereq and step_state(job, prereq) not in ("completed", "partial"):
        return False
    return True


def step_status_icon(state: str) -> str:
    icons = {
        "completed": "✅",
        "partial": "⚠️",
        "failed": "❌",
        "running": "⏳",
        "needs_user_input": "🟡",
        "skipped": "⏭️",
        "pending": "⬜",
    }
    return icons.get(state, "⬜")


def format_authors(authors: list[str]) -> str:
    if not authors:
        return "Unknown"
    if len(authors) == 1:
        return authors[0]
    return f"{authors[0]} + {len(authors) - 1} more"


# ── Main App ─────────────────────────────────────────────────────────────────

def main() -> None:
    init_session()
    st.title("PaperForge Agent")
    st.caption("AI Paper Research & Interview Project Incubator")

    data_dir = get_data_dir()

    # ── Sidebar ──────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Workflow Phases")
        for phase_id, (title, desc) in PHASES.items():
            icon = ""
            if phase_id < st.session_state.active_phase:
                icon = "✅ "
            elif phase_id == st.session_state.active_phase:
                icon = "▶️ "
            st.markdown(f"**{icon}{title}**")
            st.caption(desc)

        st.divider()
        st.caption(f"Data: `{data_dir}`")
        auto = st.checkbox("Auto-run next step after completion", value=st.session_state.auto_run)
        if auto != st.session_state.auto_run:
            st.session_state.auto_run = auto

    # ── Input area ───────────────────────────────────────────────────────
    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            default_input = os.getenv("PAPERFORGE_DEMO_INPUT", "https://arxiv.org/abs/1706.03762")
            paper_input = st.text_input("Paper title, arXiv ID, or URL", value=default_input)
        with col2:
            use_query_planner = st.checkbox("Use LLM query planner", value=True)

    # ── Job selector ─────────────────────────────────────────────────────
    jobs = list_jobs()
    if jobs:
        job_labels = {
            job.id: f"{job.metadata.title if job.metadata else job.input_text} [{job.status}]"
            for job in jobs
        }
        current_id = st.session_state.active_job_id
        job_ids = [job.id for job in jobs]
        default_idx = max(0, job_ids.index(current_id)) if current_id in job_ids else 0

        selected = st.selectbox(
            "Active Research Job",
            options=job_ids,
            index=default_idx,
            format_func=lambda jid: job_labels[jid],
        )
        if selected != st.session_state.active_job_id:
            st.session_state.active_job_id = selected
            st.rerun()

        active_job = next(job for job in jobs if job.id == selected)
    else:
        active_job = None

    st.divider()

    # ── Action panels ────────────────────────────────────────────────────
    if active_job and active_job.metadata:
        render_workflow(active_job, data_dir)
    elif active_job:
        st.info("Intake is running or in a partial state. Check timeline below.")
    else:
        st.info('Enter a paper identifier above and click "Start Intake" to begin.')

    # ── Intake button (always available) ────────────────────────────────
    st.divider()
    if st.button("Start Intake", type="primary", key="btn_intake", use_container_width=True):
        if paper_input.strip():
            with st.spinner("Resolving paper identity and creating workspace..."):
                job = run_paper_intake(paper_input.strip(), use_query_planner=use_query_planner)
            st.session_state.active_job_id = job.id
            st.session_state.active_phase = 2
            st.success(f"Intake complete: {job.metadata.title if job.metadata else job.paper_slug}")
            st.rerun()
        else:
            st.warning("Please enter a paper title, arXiv ID, or URL.")

    # ── Batch intake ─────────────────────────────────────────────────────
    with st.expander("Batch Intake (multi-paper)", expanded=False):
        batch_input = st.text_area("One paper per line", height=80, key="batch_input")
        if st.button("Run Batch Intake"):
            if batch_input.strip():
                with st.spinner("Batch intaking..."):
                    batch = run_batch_intake(batch_input, use_query_planner=use_query_planner)
                st.success(f"Batch complete: {batch.total_inputs} papers, status={batch.status}")
                first_job_id = next((item.job_id for item in batch.items if item.job_id), None)
                if first_job_id:
                    st.session_state.active_job_id = first_job_id
                    st.rerun()

    # ── Timeline & artifacts ─────────────────────────────────────────────
    if active_job:
        render_job_detail(active_job, data_dir)


# ── Workflow rendering ───────────────────────────────────────────────────────

def render_workflow(job: ResearchJob, data_dir: Path):
    """Render phase-organized action buttons with progressive disclosure."""
    # Determine which phase we're in
    current_phase = _detect_phase(job)
    st.session_state.active_phase = current_phase

    # Progress bar
    completed_count = sum(
        1 for s in job.steps if s.state in ("completed", "partial")
    )
    total_steps = len(ACTIONS)
    st.progress(min(completed_count / max(total_steps, 1), 1.0),
                text=f"Progress: {completed_count}/{total_steps} steps completed")

    # Render phases
    for phase_id in range(1, 6):
        title, desc = PHASES[phase_id]
        phase_actions = [a for a in ACTIONS if a.phase == phase_id]

        # Show phases up to current + 1
        if phase_id > current_phase + 1:
            continue

        expanded = phase_id <= current_phase
        with st.expander(f"{title} — {desc}", expanded=expanded):
            # Determine how many columns
            cols = st.columns(min(len(phase_actions), 3))
            for i, action in enumerate(phase_actions):
                col_idx = i % 3
                with cols[col_idx]:
                    state = step_state(job, action.key)
                    available = is_step_available(job, action)

                    # Build button label with status
                    icon = step_status_icon(state)
                    btn_label = f"{icon} {action.label}"

                    if state == "completed":
                        st.success(btn_label)
                    elif state in ("partial", "failed"):
                        st.warning(btn_label)

                    disabled = not available and state == "pending"
                    if action.key == "intake":
                        # Intake is handled separately
                        continue

                    # Special inputs for certain steps
                    extra_input = None
                    if action.key == "enrich_sources":
                        extra_input = st.text_area(
                            "External URLs (one per line)", height=60,
                            key=f"urls_{action.key}"
                        )
                    elif action.key == "write_code_mapping":
                        extra_input = st.text_input(
                            "Local code repo path", key=f"repo_{action.key}"
                        )
                    elif action.key == "search_evidence":
                        extra_input = st.text_input(
                            "Search query", value="method experiment",
                            key=f"query_{action.key}"
                        )

                    if st.button(
                        btn_label if state == "pending" else f"↻ {action.label}",
                        key=f"btn_{action.key}",
                        disabled=disabled,
                        use_container_width=True,
                        type="primary" if state == "pending" and available else "secondary",
                    ):
                        with st.spinner(f"Running: {action.label}..."):
                            try:
                                updated = _run_action(action, job, extra_input)
                                # Refresh job from storage for accurate state
                                jobs = list_jobs()
                                refreshed = next((j for j in jobs if j.id == job.id), job)
                                job.steps = refreshed.steps
                                job.artifacts = refreshed.artifacts
                                job.status = refreshed.status
                            except Exception as e:
                                st.error(f"Failed: {e}")
                        st.rerun()


def _run_action(action: ActionStep, job: ResearchJob, extra_input: str | None) -> ResearchJob:
    """Execute an action step with appropriate arguments."""
    if action.key == "enrich_sources":
        urls = [u.strip() for u in (extra_input or "").splitlines() if u.strip()]
        return run_source_enrichment(job, user_source_urls=urls)
    if action.key == "write_code_mapping":
        repo = str(extra_input).strip() if extra_input else None
        return run_code_mapping_evidence(job, code_repo_path=repo)
    if action.key == "search_evidence":
        query = str(extra_input).strip() if extra_input else "method experiment"
        return run_evidence_search(job, query)
    return action.fn(job)


def _detect_phase(job: ResearchJob) -> int:
    """Detect current phase from completed steps."""
    # Check phases in reverse to find the highest active phase
    phase_completion = {}
    for phase_id in range(1, 6):
        phase_actions = [a for a in ACTIONS if a.phase == phase_id]
        states = [step_state(job, a.key) for a in phase_actions]
        completed = sum(1 for s in states if s in ("completed", "partial"))
        phase_completion[phase_id] = completed / max(len(phase_actions), 1)

    for phase_id in range(1, 6):
        if phase_completion[phase_id] < 0.8:
            return phase_id
    return 5


# ── Job detail rendering ─────────────────────────────────────────────────────

def render_job_detail(job: ResearchJob, data_dir: Path):
    """Render job summary, timeline, and artifacts."""
    st.divider()
    metadata = job.metadata

    col1, col2, col3 = st.columns([1.2, 1, 1])

    with col1:
        st.subheader("Paper Workspace")
        if metadata:
            st.markdown(f"**Title:** {metadata.title}")
            st.markdown(f"**Slug:** `{metadata.slug}`")
            st.markdown(f"**Venue:** {metadata.venue or 'Unknown'}")
            st.markdown(f"**Year:** {metadata.year or 'Unknown'}")
            st.markdown(f"**Authors:** {format_authors(metadata.authors)}")
            if metadata.abstract:
                with st.expander("Abstract"):
                    st.write(metadata.abstract)
        else:
            st.write(job.input_text)

    with col2:
        st.subheader("Agent Timeline")
        if not job.steps:
            st.write("No steps recorded yet.")
        for step in job.steps:
            icon = step_status_icon(step.state)
            st.markdown(f"{icon} **{step.name}**")
            st.caption(f"State: `{step.state}`")
            if step.error:
                st.warning(step.error)

    with col3:
        st.subheader("Artifacts")
        if not job.artifacts:
            st.write("No artifacts yet.")
        for artifact in job.artifacts:
            artifact_path = data_dir / artifact.path
            st.markdown(f"**{artifact.label}**")
            st.code(str(artifact_path), language="text")
            if artifact_path.exists():
                suffix = artifact_path.suffix.lower()
                if suffix in {".md", ".json", ".txt"}:
                    with st.expander(f"Preview: {artifact_path.name}"):
                        try:
                            st.text(artifact_path.read_text(encoding="utf-8"))
                        except Exception:
                            st.caption("(binary or unreadable)")
                elif suffix in {".png", ".jpg", ".jpeg", ".webp"}:
                    st.image(str(artifact_path), caption=artifact.label)


if __name__ == "__main__":
    main()
