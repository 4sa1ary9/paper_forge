from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from paperforge.asset_collector import run_asset_collection
from paperforge.code_linker import run_code_linking
from paperforge.doubts_agent import run_doubts_scaffold
from paperforge.interview_mapper import run_interview_mapping_scaffold
from paperforge.intake_agent import run_paper_intake
from paperforge.note_writer import run_note_writing
from paperforge.package_validator import run_package_validation
from paperforge.pdf_image_extractor import run_pdf_image_extraction
from paperforge.source_enrichment import run_source_enrichment
from paperforge.storage import get_data_dir, list_jobs
from paperforge.terminology_agent import run_terminology_scaffold


st.set_page_config(
    page_title="PaperForge Agent",
    page_icon="PF",
    layout="wide",
)


def main() -> None:
    st.title("PaperForge Agent")
    st.caption("AI 论文研究与面试项目孵化助手")

    data_dir = get_data_dir()
    st.info(f"当前数据目录：`{data_dir}`")

    with st.sidebar:
        st.header("Workflow")
        st.markdown(
            """
            1. 输入论文标题或 arXiv 链接
            2. Agent 解析论文身份
            3. 创建 paper workspace
            4. 写入 metadata 和 source log
            5. 下载 PDF 和 TeX Source
            6. 提取 PDF 图片
            7. 整理外部资料来源
            8. 整理代码仓库候选
            9. 生成论文笔记骨架
            10. 生成术语库骨架
            11. 生成疑难点骨架
            12. 生成面试项目映射骨架
            13. 验证研究包状态
            14. 展示 timeline 和 artifacts
            """
        )

    default_input = os.getenv("PAPERFORGE_DEMO_INPUT", "https://arxiv.org/abs/1706.03762")
    paper_input = st.text_area(
        "论文标题、arXiv ID 或 URL",
        value=default_input,
        height=110,
    )

    if st.button("Start Intake", type="primary"):
        if paper_input.strip():
            with st.spinner("Agent 正在解析论文并创建研究工作区..."):
                job = run_paper_intake(paper_input.strip())
            st.success(f"Intake 完成：{job.paper_slug}")
            st.session_state["active_job_id"] = job.id
        else:
            st.warning("请输入论文标题、arXiv ID 或 URL。")

    jobs = list_jobs()
    if not jobs:
        st.divider()
        st.write("还没有研究任务。先输入一篇论文开始。")
        return

    active_job_id = st.session_state.get("active_job_id", jobs[0].id)
    job_labels = {
        job.id: f"{job.metadata.title if job.metadata else job.input_text} [{job.status}]"
        for job in jobs
    }

    selected_job_id = st.selectbox(
        "研究任务",
        options=[job.id for job in jobs],
        index=max(0, [job.id for job in jobs].index(active_job_id)) if active_job_id in job_labels else 0,
        format_func=lambda job_id: job_labels[job_id],
    )
    st.session_state["active_job_id"] = selected_job_id
    active_job = next(job for job in jobs if job.id == selected_job_id)

    if active_job.metadata and st.button("Collect Assets"):
        with st.spinner("Asset Collector 正在下载论文资产..."):
            active_job = run_asset_collection(active_job)
        st.success(f"Asset collection finished: {active_job.status}")

    if active_job.metadata and st.button("Extract PDF Images"):
        with st.spinner("PDF Image Extractor 正在提取图片..."):
            active_job = run_pdf_image_extraction(active_job)
        st.success(f"PDF image extraction finished: {active_job.status}")

    user_source_text = st.text_area(
        "外部资料 URL（可选，每行一个）",
        value="",
        height=80,
    )
    if active_job.metadata and st.button("Enrich Sources"):
        source_urls = [line.strip() for line in user_source_text.splitlines() if line.strip()]
        with st.spinner("Source Enrichment Agent 正在整理外部资料..."):
            active_job = run_source_enrichment(active_job, source_urls)
        st.success("Source enrichment finished.")

    if active_job.metadata and st.button("Link Code Candidates"):
        with st.spinner("Code Linker Agent 正在整理代码仓库候选..."):
            active_job = run_code_linking(active_job)
        st.success(f"Code linking finished: {active_job.status}")

    if active_job.metadata and st.button("Write Note Scaffold"):
        with st.spinner("Note Writer Agent 正在生成笔记骨架..."):
            active_job = run_note_writing(active_job)
        st.success("Note scaffold written.")

    if active_job.metadata and st.button("Write Terminology Scaffold"):
        with st.spinner("Terminology Agent 正在生成术语库骨架..."):
            active_job = run_terminology_scaffold(active_job)
        st.success("Terminology scaffold written.")

    if active_job.metadata and st.button("Write Doubts Scaffold"):
        with st.spinner("Doubts Agent 正在生成疑难点骨架..."):
            active_job = run_doubts_scaffold(active_job)
        st.success("Doubts scaffold written.")

    if active_job.metadata and st.button("Write Interview Mapping Scaffold"):
        with st.spinner("Interview Mapper Agent 正在生成面试项目映射骨架..."):
            active_job = run_interview_mapping_scaffold(active_job)
        st.success("Interview mapping scaffold written.")

    if active_job.metadata and st.button("Validate Research Package"):
        with st.spinner("Research Package Validator 正在检查研究包产物..."):
            active_job = run_package_validation(active_job)
        st.success(f"Research package validation finished: {active_job.status}")

    render_job(active_job, data_dir)


def render_job(job, data_dir: Path) -> None:
    metadata = job.metadata
    st.divider()

    summary_col, timeline_col, artifact_col = st.columns([1.3, 1, 1])

    with summary_col:
        st.subheader("Paper Workspace")
        if metadata:
            st.markdown(f"**Title:** {metadata.title}")
            st.markdown(f"**Slug:** `{metadata.slug}`")
            st.markdown(f"**Venue:** {metadata.venue or 'Unknown'}")
            st.markdown(f"**Year:** {metadata.year or 'Unknown'}")
            st.markdown(f"**Authors:** {format_authors(metadata.authors)}")
            if metadata.abstract:
                st.markdown("**Abstract:**")
                st.write(metadata.abstract)
        else:
            st.write(job.input_text)

    with timeline_col:
        st.subheader("Agent Timeline")
        for step in job.steps:
            icon = state_icon(step.state)
            st.markdown(f"{icon} **{step.name}**")
            st.caption(f"State: `{step.state}`")
            if step.error:
                st.warning(step.error)

    with artifact_col:
        st.subheader("Artifacts")
        if not job.artifacts:
            st.write("No artifacts yet.")
        for artifact in job.artifacts:
            artifact_path = data_dir / artifact.path
            st.markdown(f"**{artifact.label}**")
            st.code(str(artifact_path), language="text")
            if artifact_path.exists() and artifact_path.suffix in {".md", ".json"}:
                with st.expander("Preview"):
                    st.text(artifact_path.read_text(encoding="utf-8"))
            if artifact_path.exists() and artifact_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                st.image(str(artifact_path), caption=artifact.label)


def format_authors(authors: list[str]) -> str:
    if not authors:
        return "Unknown"
    if len(authors) == 1:
        return authors[0]
    return f"{authors[0]} + {len(authors) - 1} more"


def state_icon(state: str) -> str:
    return {
        "completed": "✅",
        "partial": "⚠️",
        "failed": "❌",
        "running": "⏳",
        "needs_user_input": "🟡",
        "skipped": "⏭️",
    }.get(state, "⬜")


if __name__ == "__main__":
    main()
