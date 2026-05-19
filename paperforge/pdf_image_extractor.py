from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


@dataclass
class ExtractedPdfImage:
    path: Path
    page: int
    width: int
    height: int
    source_xref: int | None


PdfImageExtractor = Callable[[Path, Path], list[ExtractedPdfImage]]


def run_pdf_image_extraction(
    job: ResearchJob,
    extractor: PdfImageExtractor | None = None,
) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("PDF image extraction requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    images_dir = paper_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    step = start_step(create_step("pdf.extract_images", "Extract PDF images", ["raw/paper.pdf"]))
    job.steps.append(step)

    pdf_path = _find_pdf_path(job)
    if pdf_path is None:
        finish_step(step, "skipped", [], "PDF asset is not available")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        extracted_images = (extractor or extract_images_with_pymupdf)(pdf_path, images_dir)
        manifest_path = images_dir / "manifest.md"
        manifest_path.write_text(_manifest_markdown(extracted_images), encoding="utf-8")
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    for image in extracted_images:
        _add_artifact(job, "figure", image.path, "Extracted PDF image")
    _add_artifact(job, "note", manifest_path, "Extracted image manifest")

    outputs = [relative_to_data_dir(image.path) for image in extracted_images]
    outputs.append(relative_to_data_dir(manifest_path))
    if extracted_images:
        finish_step(step, "completed", outputs)
    else:
        finish_step(step, "partial", outputs, "No images were extracted from the PDF")
        job.status = "partial"

    job.updated_at = now_iso()
    save_job(job)
    return job


def extract_images_with_pymupdf(pdf_path: Path, images_dir: Path) -> list[ExtractedPdfImage]:
    try:
        import pymupdf
    except ImportError as error:
        raise RuntimeError("PyMuPDF is required for PDF image extraction") from error

    images: list[ExtractedPdfImage] = []
    with pymupdf.open(pdf_path) as document:
        image_index = 1
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            for page_image_index, image_info in enumerate(page.get_images(full=True), start=1):
                xref = image_info[0]
                image_data = document.extract_image(xref)
                width = int(image_data.get("width", 0))
                height = int(image_data.get("height", 0))
                if width < 160 or height < 120:
                    continue

                extension = _safe_extension(str(image_data.get("ext") or "png"))
                image_path = images_dir / (
                    f"fig{image_index:03d}_page{page_index + 1}_img{page_image_index}.{extension}"
                )
                if not image_path.exists():
                    image_path.write_bytes(image_data["image"])
                images.append(ExtractedPdfImage(image_path, page_index + 1, width, height, xref))
                image_index += 1

        if images:
            return images

        for page_index in range(min(document.page_count, 12)):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
            image_path = images_dir / f"fig{image_index:03d}_page{page_index + 1}_snapshot.png"
            if not image_path.exists():
                pixmap.save(image_path)
            images.append(
                ExtractedPdfImage(
                    path=image_path,
                    page=page_index + 1,
                    width=pixmap.width,
                    height=pixmap.height,
                    source_xref=None,
                )
            )
            image_index += 1
    return images


def _find_pdf_path(job: ResearchJob) -> Path | None:
    data_dir = get_data_dir()
    for artifact in job.artifacts:
        if artifact.kind == "pdf":
            candidate = data_dir / artifact.path
            if candidate.exists():
                return candidate

    if job.metadata is None:
        return None

    fallback = get_paper_vault_dir() / job.metadata.slug / "raw" / "paper.pdf"
    if fallback.exists():
        return fallback
    return None


def _manifest_markdown(images: list[ExtractedPdfImage]) -> str:
    lines = [
        "# Extracted Figures",
        "",
        "| Index | File | Page | Size | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    if not images:
        lines.append("| - | No images extracted | - | - | - |")
        lines.append("")
        return "\n".join(lines)

    for index, image in enumerate(images, start=1):
        source = str(image.source_xref) if image.source_xref is not None else "page-render"
        lines.append(
            f"| {index} | `{image.path.name}` | {image.page} | {image.width}x{image.height} | {source} |"
        )
    lines.append("")
    return "\n".join(lines)


def _safe_extension(extension: str) -> str:
    lowered = extension.lower()
    if lowered in {"png", "jpg", "jpeg", "bmp", "tiff", "jp2"}:
        return lowered
    return "bin"


def _add_artifact(job: ResearchJob, kind: str, path: Path, label: str) -> None:
    artifact_path = relative_to_data_dir(path)
    if any(artifact.path == artifact_path for artifact in job.artifacts):
        return
    job.artifacts.append(Artifact(kind, artifact_path, label))
