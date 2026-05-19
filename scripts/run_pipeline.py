"""
Run a real arXiv paper through the full pipeline:
  intake -> asset collection -> PDF image extraction

Usage: uv run python scripts/run_pipeline.py [arxiv_id_or_url]
Default: 2006.11239 (DDPM paper)
"""

import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paperforge.intake_agent import run_paper_intake
from paperforge.asset_collector import run_asset_collection
from paperforge.pdf_image_extractor import run_pdf_image_extraction
from paperforge.storage import save_job

DEFAULT_INPUT = "https://arxiv.org/abs/2006.11239"
INPUT_TEXT = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT

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
print(f"{STAGE_SEP}\n  STAGE 3 — PDF IMAGE EXTRACTION\n{STAGE_SEP}")

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

# ── Summary ─────────────────────────────────────────────────────────
print(f"{STAGE_SEP}\n  PIPELINE COMPLETE\n{STAGE_SEP}")
print(f"\n  Paper: {job.metadata.title}")
print(f"  Vault: .paperforge-data/paper-vault/{job.paper_slug}/")
print(f"  Job ID: {job.id}")
