from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


GITHUB_REPOSITORY_PATTERN = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
    flags=re.I,
)
CODE_MAPPING_HEADING = "## Code Mapping Evidence"
CODE_FILE_EXTENSIONS = {
    ".py",
    ".ipynb",
    ".js",
    ".ts",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".cc",
    ".c",
    ".h",
    ".hpp",
    ".cu",
    ".m",
    ".yaml",
    ".yml",
    ".toml",
}
EXCLUDED_CODE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".paperforge-data",
}
METHOD_MARKERS = [
    "attention",
    "multi-head attention",
    "self attention",
    "positional encoding",
    "embedding",
    "encoder",
    "decoder",
    "transformer",
    "architecture",
    "model",
    "training",
    "loss",
    "optimizer",
    "diffusion",
    "denoising",
    "unet",
    "noise schedule",
    "sampler",
    "score matching",
    "latent",
    "retrieval",
    "ranking",
    "generation",
]
MAX_CODE_FILES = 120
MAX_CODE_FILE_BYTES = 200_000
MAX_CODE_FILE_READ_CHARS = 30_000
MAX_MAPPING_RESULTS = 8


@dataclass(frozen=True)
class CodeFileMatch:
    relative_path: str
    matched_terms: list[str]
    score: int


@dataclass(frozen=True)
class CodeSymbolMatch:
    relative_path: str
    symbol_name: str
    symbol_type: str
    matched_terms: list[str]
    confidence: str
    score: int


def run_code_linking(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Code linking requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "code-references.md"

    step = start_step(
        create_step(
            "code.link_repositories",
            "Link code repositories",
            ["metadata.github_candidates", "notes/external-sources.md"],
        )
    )
    job.steps.append(step)

    candidates = _github_candidates(job)
    output_path.write_text(_code_references_markdown(job, candidates), encoding="utf-8")
    _add_artifact(job, output_path)

    outputs = [relative_to_data_dir(output_path)]
    if candidates:
        finish_step(step, "completed", outputs)
    else:
        finish_step(step, "partial", outputs, "No GitHub repository candidates were found")
        job.status = "partial"

    job.updated_at = now_iso()
    save_job(job)
    return job


def run_code_mapping_evidence(job: ResearchJob, code_repo_path: str | Path | None = None) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Code mapping requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    code_references_path = notes_dir / "code-references.md"
    readme_path = notes_dir / "README.md"

    step = start_step(
        create_step(
            "code.map_evidence",
            "Map paper method evidence to code paths",
            [
                "notes/code-references.md",
                "notes/README.md",
                "user-provided local code repository",
            ],
        )
    )
    job.steps.append(step)

    missing_inputs = _missing_inputs([code_references_path, readme_path])
    if missing_inputs:
        finish_step(step, "partial", [], f"Missing code mapping inputs: {', '.join(missing_inputs)}")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    if code_repo_path is None or not str(code_repo_path).strip():
        _write_code_mapping_section(code_references_path, _needs_user_input_lines())
        _add_artifact(job, code_references_path)
        output = relative_to_data_dir(code_references_path)
        finish_step(
            step,
            "needs_user_input",
            [output],
            "No local code repository path was provided; automatic clone is disabled",
        )
        job.status = "needs_user_input"
        job.updated_at = now_iso()
        save_job(job)
        return job

    code_repo = Path(code_repo_path).expanduser().resolve()
    if not code_repo.is_dir():
        _write_code_mapping_section(code_references_path, _invalid_repo_lines(code_repo))
        _add_artifact(job, code_references_path)
        output = relative_to_data_dir(code_references_path)
        finish_step(step, "partial", [output], "Local code repository path does not exist or is not a directory")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        readme = readme_path.read_text(encoding="utf-8")
        method_terms = _method_terms_from_readme(readme)
        matches = _rank_code_files(code_repo, method_terms) if method_terms else []
        symbol_matches = _rank_python_symbols(code_repo, method_terms) if method_terms else []
        lines = _code_mapping_lines(code_repo, method_terms, matches, symbol_matches)
        _write_code_mapping_section(code_references_path, lines)
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, code_references_path)
    output = relative_to_data_dir(code_references_path)
    if matches or symbol_matches:
        finish_step(step, "completed", [output])
    else:
        finish_step(step, "partial", [output], "No code files matched method evidence terms")
        job.status = "partial"

    job.updated_at = now_iso()
    save_job(job)
    return job


def _github_candidates(job: ResearchJob) -> list[str]:
    found: list[str] = []
    if job.metadata is not None:
        found.extend(job.metadata.github_candidates)

    source_log = _external_sources_path(job)
    if source_log and source_log.exists():
        found.extend(_extract_github_urls(source_log.read_text(encoding="utf-8")))

    return _deduplicate(found)


def _extract_github_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in GITHUB_REPOSITORY_PATTERN.finditer(text):
        owner, repo = match.groups()
        urls.append(f"https://github.com/{owner}/{repo}".rstrip(".,)"))
    return urls


def _external_sources_path(job: ResearchJob) -> Path | None:
    data_dir = get_data_dir()
    for artifact in job.artifacts:
        if artifact.path.endswith("notes/external-sources.md"):
            return data_dir / artifact.path

    if job.metadata is None:
        return None
    return get_paper_vault_dir() / job.metadata.slug / "notes" / "external-sources.md"


def _code_references_markdown(job: ResearchJob, candidates: list[str]) -> str:
    title = job.metadata.title if job.metadata else job.input_text
    lines = [
        "# Code References",
        "",
        f"- Paper: {title}",
        "- Clone decision: not cloned",
        "- Reason: first MVP only records candidates; cloning requires user confirmation.",
        "",
        "## Repository Candidates",
        "",
    ]

    if not candidates:
        lines.extend(
            [
                "- No GitHub repository candidates found yet.",
                "",
                "## Next Manual Step",
                "",
                "- Add an official GitHub URL through Source Enrichment or metadata before cloning.",
                "",
            ]
        )
        return "\n".join(lines)

    for index, url in enumerate(candidates, start=1):
        lines.extend(
            [
                f"### Candidate {index}",
                "",
                f"- Repository URL: {url}",
                "- License: not checked",
                "- Main tech stack: not checked",
                "- Core files: not checked",
                "- Method-to-code mapping: not checked",
                "- Reproduction difficulty: not checked",
                "- Suggested reading path: not checked",
                "- Reliability: candidate",
                "",
            ]
        )
    return "\n".join(lines)


def _deduplicate(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        clean = url.strip().rstrip("/")
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
    return result


def _missing_inputs(paths: list[Path]) -> list[str]:
    return [path.name for path in paths if not path.exists()]


def _method_terms_from_readme(markdown: str) -> list[str]:
    core_method = _section_body(markdown, "Core Method")
    searchable = _normalize_search_text(core_method)
    terms = [term for term in METHOD_MARKERS if _term_in_text(term, searchable)]
    return terms or _fallback_terms(core_method)


def _section_body(markdown: str, section: str) -> str:
    pattern = re.compile(rf"^## {re.escape(section)}\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(markdown)
    return match.group(1) if match else ""


def _fallback_terms(text: str) -> list[str]:
    normalized = _normalize_search_text(text)
    words = [
        word
        for word in normalized.split()
        if len(word) >= 6 and word not in {"method", "evidence", "manual", "review", "generated"}
    ]
    result: list[str] = []
    for word in words:
        if word not in result:
            result.append(word)
    return result[:8]


def _rank_code_files(code_repo: Path, method_terms: list[str]) -> list[CodeFileMatch]:
    matches: list[CodeFileMatch] = []
    for path in _iter_code_files(code_repo):
        relative_path = path.relative_to(code_repo).as_posix()
        text = _read_code_text(path)
        searchable = _normalize_search_text(f"{relative_path}\n{text}")
        matched_terms = [term for term in method_terms if _term_in_text(term, searchable)]
        if not matched_terms:
            continue
        normalized_path = _normalize_search_text(relative_path)
        path_bonus = sum(1 for term in matched_terms if _term_in_text(term, normalized_path))
        matches.append(
            CodeFileMatch(
                relative_path=relative_path,
                matched_terms=matched_terms,
                score=len(matched_terms) * 2 + path_bonus,
            )
        )
    return sorted(matches, key=lambda match: (-match.score, match.relative_path))[:MAX_MAPPING_RESULTS]


def _rank_python_symbols(code_repo: Path, method_terms: list[str]) -> list[CodeSymbolMatch]:
    matches: list[CodeSymbolMatch] = []
    for path in _iter_code_files(code_repo):
        if path.suffix.lower() != ".py":
            continue
        relative_path = path.relative_to(code_repo).as_posix()
        text = _read_code_text(path)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbol_type = "class"
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                symbol_type = "function"
            else:
                continue
            source = _node_source_text(text, node)
            searchable = _normalize_search_text(f"{relative_path}\n{node.name}\n{source}")
            matched_terms = [term for term in method_terms if _term_in_text(term, searchable)]
            if not matched_terms:
                continue
            normalized_symbol = _normalize_search_text(node.name)
            symbol_bonus = sum(1 for term in matched_terms if _term_in_text(term, normalized_symbol))
            score = len(matched_terms) * 2 + symbol_bonus
            matches.append(
                CodeSymbolMatch(
                    relative_path=relative_path,
                    symbol_name=node.name,
                    symbol_type=symbol_type,
                    matched_terms=matched_terms,
                    confidence=_symbol_confidence(len(matched_terms), symbol_bonus),
                    score=score,
                )
            )
    return sorted(
        matches,
        key=lambda match: (-match.score, match.relative_path, match.symbol_type, match.symbol_name),
    )[:MAX_MAPPING_RESULTS]


def _node_source_text(text: str, node: ast.AST) -> str:
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        return ""
    lines = text.splitlines()
    start = max(0, node.lineno - 1)
    end = min(len(lines), node.end_lineno)
    return "\n".join(lines[start:end])


def _symbol_confidence(matched_count: int, symbol_bonus: int) -> str:
    if matched_count >= 2 or symbol_bonus > 0:
        return "medium"
    return "low"


def _iter_code_files(code_repo: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(code_repo.rglob("*")):
        if len(files) >= MAX_CODE_FILES:
            break
        if not path.is_file() or path.suffix.lower() not in CODE_FILE_EXTENSIONS:
            continue
        if any(part in EXCLUDED_CODE_DIRS for part in path.relative_to(code_repo).parts):
            continue
        try:
            if path.stat().st_size > MAX_CODE_FILE_BYTES:
                continue
        except OSError:
            continue
        files.append(path)
    return files


def _read_code_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")[:MAX_CODE_FILE_READ_CHARS]


def _normalize_search_text(text: str) -> str:
    split_camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    lowered = split_camel.lower().replace("_", " ").replace("-", " ")
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def _term_in_text(term: str, normalized_text: str) -> bool:
    normalized_term = _normalize_search_text(term)
    return f" {normalized_term} " in f" {normalized_text} "


def _needs_user_input_lines() -> list[str]:
    return [
        CODE_MAPPING_HEADING,
        "",
        "- Mapping status: needs user input",
        "- Required input: provide a local code repository path or confirm a clone/read strategy.",
        "- Clone decision: not cloned by PaperForge.",
        "- Method-to-code mapping: not generated.",
    ]


def _invalid_repo_lines(code_repo: Path) -> list[str]:
    return [
        CODE_MAPPING_HEADING,
        "",
        "- Mapping status: partial",
        f"- Local code path checked: `{code_repo}`",
        "- Problem: path does not exist or is not a directory.",
        "- Clone decision: not cloned by PaperForge.",
        "- Method-to-code mapping: not generated.",
    ]


def _code_mapping_lines(
    code_repo: Path,
    method_terms: list[str],
    matches: list[CodeFileMatch],
    symbol_matches: list[CodeSymbolMatch],
) -> list[str]:
    lines = [
        CODE_MAPPING_HEADING,
        "",
        "- Mapping status: evidence-backed local scan" if matches or symbol_matches else "- Mapping status: partial",
        f"- Local code path: `{code_repo}`",
        "- Clone decision: not cloned by PaperForge; local path supplied by user.",
        "- Method evidence source: `notes/README.md`, Core Method section.",
        f"- Method terms used: {_term_list(method_terms)}",
        "",
        "### Candidate Code Paths",
        "",
    ]

    if not method_terms:
        lines.extend(
            [
                "- No method terms were found in `notes/README.md` Core Method evidence.",
                "",
                "### Boundary",
                "",
                "- This MVP does not infer mappings without paper-side method terms.",
            ]
        )
        return lines

    if not matches:
        lines.extend(
            [
                "- No local code files matched the paper-side method terms.",
                "",
                "### Boundary",
                "",
                "- This MVP only reports candidate files when paper method terms overlap with local code paths or contents.",
            ]
        )
        return lines

    for index, match in enumerate(matches, start=1):
        lines.extend(
            [
                f"{index}. `{match.relative_path}`",
                f"   - Matched method terms: {_term_list(match.matched_terms)}",
                "   - Why it may matter: file path or content overlaps with the paper's Core Method evidence.",
                "   - Needs human review: confirm this file actually implements the cited method before final notes.",
            ]
        )

    lines.extend(
        [
            "",
            "### Candidate Symbols",
            "",
        ]
    )
    if not symbol_matches:
        lines.extend(
            [
                "- No Python function or class symbols matched the paper-side method terms.",
                "",
            ]
        )
    else:
        for index, match in enumerate(symbol_matches, start=1):
            lines.extend(
                [
                    f"{index}. `{match.symbol_name}`",
                    f"   - File path: `{match.relative_path}`",
                    f"   - Symbol name: `{match.symbol_name}`",
                    f"   - Symbol type: {match.symbol_type}",
                    f"   - Matched method terms: {_term_list(match.matched_terms)}",
                    f"   - Confidence: {match.confidence}",
                    "   - Boundary: symbol-level candidate only; confirm manually before treating it as an implementation mapping.",
                ]
            )

    lines.extend(
        [
            "",
            "### Boundary",
            "",
            "- This is candidate evidence only; it does not claim true implementation correspondence.",
            "- Files are ranked by deterministic method-term overlap, not by semantic code understanding.",
        ]
    )
    return lines


def _term_list(terms: list[str]) -> str:
    if not terms:
        return "not detected"
    return ", ".join(f"`{term}`" for term in terms)


def _write_code_mapping_section(path: Path, lines: list[str]) -> None:
    markdown = path.read_text(encoding="utf-8") if path.exists() else "# Code References\n"
    section = "\n".join(lines).rstrip() + "\n"
    pattern = re.compile(rf"^{re.escape(CODE_MAPPING_HEADING)}\n.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    if pattern.search(markdown):
        updated = pattern.sub(section, markdown, count=1)
    else:
        updated = markdown.rstrip() + "\n\n" + section
    path.write_text(updated.rstrip() + "\n", encoding="utf-8")


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "code_reference"
            artifact.label = "Code references"
            return
    job.artifacts.append(Artifact("code_reference", artifact_path, "Code references"))
