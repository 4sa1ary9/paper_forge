"""
Run a real arXiv paper through the full pipeline:
  intake -> asset collection -> source enrichment -> PDF image extraction
  -> code linking -> note scaffold -> terminology scaffold -> doubts scaffold
  -> interview mapping scaffold -> PDF text evidence -> package validation
  -> deep note planning

Usage: uv run python scripts/run_pipeline.py [arxiv_id_or_url] [external_source_url ...]
Default: 2006.11239 (DDPM paper)
"""

import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paperforge.intake_agent import run_paper_intake
from paperforge.asset_collector import run_asset_collection
from paperforge.source_enrichment import run_source_enrichment
from paperforge.pdf_image_extractor import run_pdf_image_extraction
from paperforge.code_linker import run_code_linking
from paperforge.note_writer import run_note_writing
from paperforge.terminology_agent import run_terminology_scaffold
from paperforge.doubts_agent import run_doubts_scaffold
from paperforge.interview_mapper import run_interview_mapping_scaffold
from paperforge.package_validator import run_package_validation
from paperforge.pdf_text_extractor import run_pdf_text_extraction
from paperforge.deep_note_planner import run_deep_note_planning

DEFAULT_INPUT = "https://arxiv.org/abs/2006.11239"
INPUT_TEXT = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
EXTERNAL_SOURCE_URLS = sys.argv[2:] if len(sys.argv) > 2 else []

STAGE_SEP = "\n" + "=" * 64

# ── Stage 1: Intake ─────────────────────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 1 — INTAKE\n  Input: {INPUT_TEXT}\n{STAGE_SEP}")

job = run_paper_intake(INPUT_TEXT)
print(f"\n  Status: {job.status}")
print(f"  Paper:  {job.metadata.title}")
print(f"  Slug:   {job.paper_slug}")
print(f"  Steps:")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}")
print(f"  Artifacts: {len(job.artifacts)}")

if job.status not in ("completed", "partial"):
    print("  [FAIL] Intake did not complete successfully — aborting.")
    sys.exit(1)

# ── Stage 2: Asset Collection ───────────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 2 — ASSET COLLECTION\n{STAGE_SEP}")

job = run_asset_collection(job)
print(f"\n  Status: {job.status}")
print(f"  Steps:")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")
print(f"  Artifacts: {len(job.artifacts)}")
for a in job.artifacts:
    print(f"    [{a.kind:12s}] {a.path}")

# ── Stage 3: PDF Image Extraction ───────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 3 — SOURCE ENRICHMENT\n{STAGE_SEP}")

job = run_source_enrichment(job, EXTERNAL_SOURCE_URLS)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Stage 4: PDF Image Extraction ───────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 4 — PDF IMAGE EXTRACTION\n{STAGE_SEP}")

job = run_pdf_image_extraction(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# Show image extraction results
images_dir = os.path.join(
    os.environ.get("PAPERFORGE_DATA_DIR", ".paperforge-data"),
    "paper-vault",
    job.paper_slug,
    "images",
)
if os.path.isdir(images_dir):
    image_files = sorted(os.listdir(images_dir))
    print(f"\n  Images extracted ({len(image_files)}):")
    for f in image_files:
        fpath = os.path.join(images_dir, f)
        size_kb = os.path.getsize(fpath) / 1024
        if f.endswith(".md"):
            print(f"    [manifest] {f}")
        else:
            print(f"    [{size_kb:6.1f} KB] {f}")
else:
    print("\n  [WARN] No images directory found.")

# ── Stage 5: Code Linking ───────────────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 5 — CODE LINKING\n{STAGE_SEP}")

job = run_code_linking(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Stage 6: Note Scaffold ──────────────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 6 — NOTE SCAFFOLD\n{STAGE_SEP}")

job = run_note_writing(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Stage 7: Terminology Scaffold ───────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 7 — TERMINOLOGY SCAFFOLD\n{STAGE_SEP}")

job = run_terminology_scaffold(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Stage 8: Doubts Scaffold ────────────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 8 — DOUBTS SCAFFOLD\n{STAGE_SEP}")

job = run_doubts_scaffold(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Stage 9: Interview Mapping Scaffold ─────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 9 — INTERVIEW MAPPING SCAFFOLD\n{STAGE_SEP}")

job = run_interview_mapping_scaffold(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Stage 10: PDF Text Evidence ──────────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 10 — PDF TEXT EVIDENCE\n{STAGE_SEP}")

job = run_pdf_text_extraction(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Stage 11: Research Package Validation ───────────────────────────
print(f"{STAGE_SEP}\n  STAGE 11 — RESEARCH PACKAGE VALIDATION\n{STAGE_SEP}")

job = run_package_validation(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Stage 12: Deep Note Planning ─────────────────────────────────────
print(f"{STAGE_SEP}\n  STAGE 12 — DEEP NOTE PLANNING\n{STAGE_SEP}")

job = run_deep_note_planning(job)
print(f"\n  Status: {job.status}")
for s in job.steps:
    print(f"    [{s.state:16s}] {s.name}  {s.error or ''}")

# ── Summary ─────────────────────────────────────────────────────────
print(f"{STAGE_SEP}\n  PIPELINE COMPLETE\n{STAGE_SEP}")
print(f"\n  Paper: {job.metadata.title}")
print(f"  Vault: .paperforge-data/paper-vault/{job.paper_slug}/")
print(f"  Job ID: {job.id}")
