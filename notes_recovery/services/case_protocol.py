from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import notes_recovery.config as config
from notes_recovery.case_contract import (
    CASE_DIR_AI_REVIEW,
    CASE_DIR_TEXT_BUNDLE,
    CASE_MANIFEST_STEM,
    PIPELINE_SUMMARY_STEM,
    RUN_MANIFEST_STEM,
)
from notes_recovery.core.pipeline import (
    redact_public_safe_payload,
    sanitize_public_safe_string,
)
from notes_recovery.io import read_text_limited
from notes_recovery.utils.text import html_to_text

MAX_JSON_CHARS = 16_000
MAX_TEXT_CHARS = 6_000
MAX_CSV_ROWS = 12
EXCERPT_CHARS = 280
TOKEN_RE = re.compile(r"[A-Za-z0-9_:-]{3,}")

DERIVED_ARTIFACT_RETRIEVAL_CONTRACT_VERSION = "2026-04-02.v1"
PRIMARY_RETRIEVAL_UNIT = "one-case-root-at-a-time"
EVIDENCE_REF_SCHEMA_VERSION = "2026-04-02.v1"
TIER_A_ANCHOR = "tier_a_anchor"
TIER_B_STRUCTURE = "tier_b_structure"
TIER_C_ENRICHER = "tier_c_enricher"

DEFAULT_TIER_A_SOURCE_IDS = (
    "review_index",
    "verification_preview",
    "pipeline_summary",
)
DEFAULT_TIER_B_SOURCE_IDS = (
    "run_manifest",
    "case_manifest",
    "timeline_summary",
)

EVIDENCE_REF_FIELDS = (
    "source_id",
    "artifact",
    "relpath",
    "kind",
    "excerpt",
    "selection_reason",
    "score",
    "locator",
)

ABSOLUTE_RETRIEVAL_EXCLUSIONS = (
    "raw copied evidence bodies",
    "live Apple Notes store",
    "DB_Backup/",
    "Cache_Backup/",
    "Spotlight_Backup/",
    "absolute paths",
    "credentials",
    "secrets",
    "broad filesystem browse",
    "unvalidated plugin outputs",
    "storefront/discovery docs as case evidence",
    "hosted retrieval by default",
    "vector retrieval by default",
    "cloud retrieval by default",
    "cross-case blended retrieval without an explicit compare contract",
)

RESOURCE_WEIGHTS = {
    "review_index": 5.0,
    "verification_preview": 5.0,
    "verification_hit": 4.5,
    "pipeline_summary": 4.0,
    "timeline_summary": 4.0,
    "timeline_events": 3.5,
    "ai_triage_summary": 3.5,
    "ai_top_findings": 3.0,
    "case_manifest": 2.5,
    "run_manifest": 2.5,
    "report_excerpt": 2.0,
    "text_bundle_inventory": 2.0,
    "ai_next_questions": 1.5,
    "demo_case_tree": 3.0,
    "demo_verification_summary": 4.0,
    "demo_operator_brief": 3.0,
}


@dataclass(frozen=True)
class RetrievalArtifactSpec:
    source_id: str
    artifact: str
    kind: str
    tier: str
    default_selection_reason: str
    mode: str = "case-root"


@dataclass(frozen=True)
class CaseResource:
    source_id: str
    artifact: str
    relpath: str
    title: str
    content: str
    kind: str

    @property
    def excerpt(self) -> str:
        text = " ".join(self.content.split())
        if len(text) <= EXCERPT_CHARS:
            return text
        return text[:EXCERPT_CHARS].rstrip() + "..."


CASE_RESOURCE_SPECS = {
    "review_index": RetrievalArtifactSpec(
        source_id="review_index",
        artifact="Review index",
        kind="review_index",
        tier=TIER_A_ANCHOR,
        default_selection_reason="Tier A anchor for one-case review flow ordering.",
    ),
    "run_manifest": RetrievalArtifactSpec(
        source_id="run_manifest",
        artifact="Run manifest",
        kind="run_manifest",
        tier=TIER_B_STRUCTURE,
        default_selection_reason="Tier B structure artifact that anchors the per-run stage ledger.",
    ),
    "case_manifest": RetrievalArtifactSpec(
        source_id="case_manifest",
        artifact="Case manifest",
        kind="case_manifest",
        tier=TIER_B_STRUCTURE,
        default_selection_reason="Tier B structure artifact that inventories derived outputs for one case root.",
    ),
    "pipeline_summary": RetrievalArtifactSpec(
        source_id="pipeline_summary",
        artifact="Pipeline summary",
        kind="pipeline_summary",
        tier=TIER_A_ANCHOR,
        default_selection_reason="Tier A anchor that summarizes the copied-evidence workflow outcome.",
    ),
    "verification_preview": RetrievalArtifactSpec(
        source_id="verification_preview",
        artifact="Verification preview",
        kind="verification_preview",
        tier=TIER_A_ANCHOR,
        default_selection_reason="Tier A anchor that provides the fastest hit-oriented review surface.",
    ),
    "timeline_summary": RetrievalArtifactSpec(
        source_id="timeline_summary",
        artifact="Timeline summary",
        kind="timeline_summary",
        tier=TIER_B_STRUCTURE,
        default_selection_reason="Tier B structure artifact that grounds chronology before stronger conclusions.",
    ),
    "timeline_events": RetrievalArtifactSpec(
        source_id="timeline_events",
        artifact="Timeline events",
        kind="timeline_events",
        tier=TIER_C_ENRICHER,
        default_selection_reason="Tier C enricher that expands chronology beyond the summary layer.",
    ),
    "report_excerpt": RetrievalArtifactSpec(
        source_id="report_excerpt",
        artifact="HTML report excerpt",
        kind="report_excerpt",
        tier=TIER_C_ENRICHER,
        default_selection_reason="Tier C enricher that adds narrative context from the generated report surface.",
    ),
    "text_bundle_inventory": RetrievalArtifactSpec(
        source_id="text_bundle_inventory",
        artifact="Text bundle inventory",
        kind="text_bundle_inventory",
        tier=TIER_C_ENRICHER,
        default_selection_reason="Tier C enricher that summarizes review-friendly bundle contents.",
    ),
    "ai_triage_summary": RetrievalArtifactSpec(
        source_id="ai_triage_summary",
        artifact="AI triage summary",
        kind="ai_triage_summary",
        tier=TIER_C_ENRICHER,
        default_selection_reason="Tier C enricher that captures prior AI triage without replacing the core case spine.",
    ),
    "ai_top_findings": RetrievalArtifactSpec(
        source_id="ai_top_findings",
        artifact="AI top findings",
        kind="ai_top_findings",
        tier=TIER_C_ENRICHER,
        default_selection_reason="Tier C enricher that captures prior AI finding summaries for the same case root.",
    ),
    "ai_next_questions": RetrievalArtifactSpec(
        source_id="ai_next_questions",
        artifact="AI next questions",
        kind="ai_next_questions",
        tier=TIER_C_ENRICHER,
        default_selection_reason="Tier C enricher that suggests follow-up inspection targets.",
    ),
}

DEMO_RESOURCE_SPECS = {
    "demo_case_tree": RetrievalArtifactSpec(
        source_id="demo_case_tree",
        artifact="Demo case tree",
        kind="demo_case_tree",
        tier=TIER_B_STRUCTURE,
        default_selection_reason="Demo-only structure artifact that shows the public-safe case layout.",
        mode="demo-only",
    ),
    "demo_verification_summary": RetrievalArtifactSpec(
        source_id="demo_verification_summary",
        artifact="Demo verification summary",
        kind="demo_verification_summary",
        tier=TIER_A_ANCHOR,
        default_selection_reason="Demo-only Tier A anchor that mirrors the safest first inspection surface.",
        mode="demo-only",
    ),
    "demo_operator_brief": RetrievalArtifactSpec(
        source_id="demo_operator_brief",
        artifact="Demo operator brief",
        kind="demo_operator_brief",
        tier=TIER_C_ENRICHER,
        default_selection_reason="Demo-only Tier C enricher that explains the copy-first workflow in plain language.",
        mode="demo-only",
    ),
}

VERIFICATION_HIT_WILDCARD_SPEC = RetrievalArtifactSpec(
    source_id="verification_hit_*",
    artifact="Verification hit preview rows",
    kind="verification_hit",
    tier=TIER_C_ENRICHER,
    default_selection_reason="Tier C enricher that preserves bounded verification-hit preview rows.",
)


def _latest_file(root_dir: Path, pattern: str) -> Path | None:
    candidates = [path for path in root_dir.rglob(pattern) if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _latest_dir(root_dir: Path, prefix: str) -> Path | None:
    candidates = [
        path for path in root_dir.iterdir() if path.is_dir() and path.name.startswith(prefix)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _rel(base: Path, path: Path | None) -> str:
    if path is None:
        return "(missing)"
    try:
        return str(path.relative_to(base))
    except Exception:
        return str(path)


def _load_json_text(path: Path | None, case_root: Path) -> str:
    if path is None or not path.exists():
        return ""
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    redacted = redact_public_safe_payload(payload, case_root)
    text = json.dumps(redacted, ensure_ascii=True, indent=2)
    if len(text) <= MAX_JSON_CHARS:
        return text

    def _bounded_json(value: Any, *, depth: int = 0) -> Any:
        if depth >= 3:
            if isinstance(value, (dict, list)):
                return "[truncated nested payload]"
            if isinstance(value, str) and len(value) > 160:
                return value[:157] + "..."
            return value
        if isinstance(value, dict):
            bounded: dict[str, Any] = {}
            items = list(value.items())
            for key, child in items[:12]:
                bounded[str(key)] = _bounded_json(child, depth=depth + 1)
            if len(items) > 12:
                bounded["__truncated_keys__"] = len(items) - 12
            return bounded
        if isinstance(value, list):
            bounded_items = [_bounded_json(child, depth=depth + 1) for child in value[:12]]
            if len(value) > 12:
                bounded_items.append(f"... {len(value) - 12} more item(s) truncated ...")
            return bounded_items
        if isinstance(value, str) and len(value) > 512:
            return value[:509] + "..."
        return value

    bounded_text = json.dumps(_bounded_json(redacted), ensure_ascii=True, indent=2)
    if len(bounded_text) <= MAX_JSON_CHARS:
        return bounded_text
    compact_text = json.dumps(_bounded_json(redacted), ensure_ascii=True, separators=(",", ":"))
    if len(compact_text) <= MAX_JSON_CHARS:
        return compact_text
    return json.dumps(
        {
            "truncated": True,
            "preview": compact_text[: MAX_JSON_CHARS - 64],
        },
        ensure_ascii=True,
    )


def _read_text(path: Path | None, case_root: Path, *, html: bool = False) -> str:
    if path is None or not path.exists():
        return ""
    text, _truncated = read_text_limited(path, MAX_TEXT_CHARS)
    if html:
        text = html_to_text(text)
    return sanitize_public_safe_string(text, case_root)


def _read_csv_rows(path: Path | None, case_root: Path, *, max_rows: int = MAX_CSV_ROWS) -> list[CaseResource]:
    if path is None or not path.exists():
        return []
    rows: list[CaseResource] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            clean_row = {
                key: sanitize_public_safe_string(str(value), case_root)
                for key, value in row.items()
            }
            artifact = f"Verification hit {idx}"
            relpath = _rel(case_root, path)
            content = json.dumps(clean_row, ensure_ascii=True, sort_keys=True)
            rows.append(
                CaseResource(
                    source_id=f"verification_hit_{idx}",
                    artifact=artifact,
                    relpath=relpath,
                    title=artifact,
                    content=content,
                    kind="verification_hit",
                )
            )
            if len(rows) >= max_rows:
                break
    return rows


def _resource(
    *,
    source_id: str,
    artifact: str,
    path: Path | None,
    root_dir: Path,
    content: str,
    kind: str,
) -> CaseResource | None:
    if not content.strip():
        return None
    relpath = _rel(root_dir, path)
    return CaseResource(
        source_id=source_id,
        artifact=artifact,
        relpath=relpath,
        title=artifact,
        content=content,
        kind=kind,
    )


def _spec_for_resource(resource: CaseResource | dict[str, Any]) -> RetrievalArtifactSpec:
    source_id = str(resource["source_id"] if isinstance(resource, dict) else resource.source_id)
    kind = str(resource["kind"] if isinstance(resource, dict) else resource.kind)
    artifact = str(resource["artifact"] if isinstance(resource, dict) else resource.artifact)
    if source_id in CASE_RESOURCE_SPECS:
        return CASE_RESOURCE_SPECS[source_id]
    if source_id in DEMO_RESOURCE_SPECS:
        return DEMO_RESOURCE_SPECS[source_id]
    if kind == "verification_hit":
        return RetrievalArtifactSpec(
            source_id=source_id,
            artifact=artifact,
            kind=kind,
            tier=TIER_C_ENRICHER,
            default_selection_reason="Tier C enricher that preserves a bounded verification-hit preview row.",
        )
    return RetrievalArtifactSpec(
        source_id=source_id,
        artifact=artifact,
        kind=kind,
        tier=TIER_C_ENRICHER,
        default_selection_reason="Tier C enricher permitted by the derived-artifact retrieval contract.",
    )


def _selection_reason(item: dict[str, Any], *, matched: bool, injected: bool) -> str:
    spec = _spec_for_resource(item)
    if matched and injected:
        return (
            f"{spec.default_selection_reason} "
            "Kept as a retrieval backbone even though stronger query matches filled the initial ranked set."
        )
    if matched:
        return f"{spec.default_selection_reason} Ranked as a direct match for the current question."
    if injected:
        return f"{spec.default_selection_reason} Added as a fallback so the one-case retrieval spine stays grounded."
    return spec.default_selection_reason


def retrieval_contract_artifacts() -> list[dict[str, str]]:
    specs = [*CASE_RESOURCE_SPECS.values(), *DEMO_RESOURCE_SPECS.values(), VERIFICATION_HIT_WILDCARD_SPEC]
    specs.sort(key=lambda item: (item.mode, item.tier, item.source_id))
    return [
        {
            "source_id": spec.source_id,
            "artifact": spec.artifact,
            "kind": spec.kind,
            "tier": spec.tier,
            "mode": spec.mode,
        }
        for spec in specs
    ]


def derived_artifact_retrieval_contract() -> dict[str, Any]:
    return {
        "version": DERIVED_ARTIFACT_RETRIEVAL_CONTRACT_VERSION,
        "primary_retrieval_unit": PRIMARY_RETRIEVAL_UNIT,
        "evidence_ref_schema_version": EVIDENCE_REF_SCHEMA_VERSION,
        "default_tier_a_source_ids": list(DEFAULT_TIER_A_SOURCE_IDS),
        "default_tier_b_source_ids": list(DEFAULT_TIER_B_SOURCE_IDS),
        "allowed_artifacts": retrieval_contract_artifacts(),
        "evidence_ref_fields": list(EVIDENCE_REF_FIELDS),
        "absolute_exclusions": list(ABSOLUTE_RETRIEVAL_EXCLUSIONS),
        "compare_contract": "case-diff",
        "plugin_contract": "plugins-validate",
        "default_cloud_vector_retrieval": "disabled",
    }


def is_case_root(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    if (path / "review_index.md").exists():
        return True
    if any(path.glob(f"{RUN_MANIFEST_STEM}_*.json")):
        return True
    if any(path.glob(f"{CASE_MANIFEST_STEM}_*.json")):
        return True
    return False


def discover_case_roots(
    *,
    case_dirs: Iterable[Path] = (),
    search_roots: Iterable[Path] = (),
) -> list[Path]:
    candidates: dict[str, Path] = {}

    def add(path: Path) -> None:
        resolved = path.expanduser().resolve()
        if is_case_root(resolved):
            candidates[str(resolved)] = resolved

    for path in case_dirs:
        add(path)

    for root in search_roots:
        resolved_root = root.expanduser().resolve()
        if not resolved_root.exists():
            continue
        add(resolved_root)
        for pattern in (f"{RUN_MANIFEST_STEM}_*.json", f"{CASE_MANIFEST_STEM}_*.json", "review_index.md"):
            for path in resolved_root.rglob(pattern):
                add(path.parent)

    return sorted(candidates.values(), key=str)


def build_case_resources(root_dir: Path, *, include_ai_review: bool = True) -> list[CaseResource]:
    root_dir = root_dir.expanduser().resolve()
    review_index = root_dir / "review_index.md"
    run_manifest = _latest_file(root_dir, f"{RUN_MANIFEST_STEM}_*.json")
    case_manifest = _latest_file(root_dir, f"{CASE_MANIFEST_STEM}_*.json")
    pipeline_summary = _latest_file(root_dir, f"{PIPELINE_SUMMARY_STEM}_*.md")
    verification_preview = _latest_file(root_dir, "verify_top*.txt")
    verification_hits = _latest_file(root_dir, "verify_hits_*.csv")
    timeline_summary = _latest_file(root_dir, "timeline_summary_*.json")
    timeline_events = _latest_file(root_dir, "timeline_events_*.json")
    report_path = _latest_file(root_dir, "report_*.html")
    text_bundle_dir = _latest_dir(root_dir, CASE_DIR_TEXT_BUNDLE)
    inventory_path = _latest_file(text_bundle_dir, "inventory_*.md") if text_bundle_dir else None
    ai_review_dir = _latest_dir(root_dir, CASE_DIR_AI_REVIEW) if include_ai_review else None
    ai_triage = ai_review_dir / "triage_summary.md" if ai_review_dir else None
    ai_findings = ai_review_dir / "top_findings.md" if ai_review_dir else None
    ai_questions = ai_review_dir / "next_questions.md" if ai_review_dir else None

    resources: list[CaseResource] = []
    maybe_resources = [
        _resource(
            source_id="review_index",
            artifact="Review index",
            path=review_index if review_index.exists() else None,
            root_dir=root_dir,
            content=_read_text(review_index if review_index.exists() else None, root_dir),
            kind="review_index",
        ),
        _resource(
            source_id="run_manifest",
            artifact="Run manifest",
            path=run_manifest,
            root_dir=root_dir,
            content=_load_json_text(run_manifest, root_dir),
            kind="run_manifest",
        ),
        _resource(
            source_id="case_manifest",
            artifact="Case manifest",
            path=case_manifest,
            root_dir=root_dir,
            content=_load_json_text(case_manifest, root_dir),
            kind="case_manifest",
        ),
        _resource(
            source_id="pipeline_summary",
            artifact="Pipeline summary",
            path=pipeline_summary,
            root_dir=root_dir,
            content=_read_text(pipeline_summary, root_dir),
            kind="pipeline_summary",
        ),
        _resource(
            source_id="verification_preview",
            artifact="Verification preview",
            path=verification_preview,
            root_dir=root_dir,
            content=_read_text(verification_preview, root_dir),
            kind="verification_preview",
        ),
        _resource(
            source_id="timeline_summary",
            artifact="Timeline summary",
            path=timeline_summary,
            root_dir=root_dir,
            content=_load_json_text(timeline_summary, root_dir),
            kind="timeline_summary",
        ),
        _resource(
            source_id="timeline_events",
            artifact="Timeline events",
            path=timeline_events,
            root_dir=root_dir,
            content=_load_json_text(timeline_events, root_dir),
            kind="timeline_events",
        ),
        _resource(
            source_id="report_excerpt",
            artifact="HTML report excerpt",
            path=report_path,
            root_dir=root_dir,
            content=_read_text(report_path, root_dir, html=True),
            kind="report_excerpt",
        ),
        _resource(
            source_id="text_bundle_inventory",
            artifact="Text bundle inventory",
            path=inventory_path,
            root_dir=root_dir,
            content=_read_text(inventory_path, root_dir),
            kind="text_bundle_inventory",
        ),
        _resource(
            source_id="ai_triage_summary",
            artifact="AI triage summary",
            path=ai_triage if ai_triage and ai_triage.exists() else None,
            root_dir=root_dir,
            content=_read_text(ai_triage if ai_triage and ai_triage.exists() else None, root_dir),
            kind="ai_triage_summary",
        ),
        _resource(
            source_id="ai_top_findings",
            artifact="AI top findings",
            path=ai_findings if ai_findings and ai_findings.exists() else None,
            root_dir=root_dir,
            content=_read_text(ai_findings if ai_findings and ai_findings.exists() else None, root_dir),
            kind="ai_top_findings",
        ),
        _resource(
            source_id="ai_next_questions",
            artifact="AI next questions",
            path=ai_questions if ai_questions and ai_questions.exists() else None,
            root_dir=root_dir,
            content=_read_text(ai_questions if ai_questions and ai_questions.exists() else None, root_dir),
            kind="ai_next_questions",
        ),
    ]
    resources.extend(item for item in maybe_resources if item is not None)
    resources.extend(_read_csv_rows(verification_hits, root_dir))
    return resources


def build_demo_resources(repo_root: Path, *, include_ai_review: bool = True) -> list[CaseResource]:
    demo_dir = repo_root / "notes_recovery" / "resources" / "demo"
    root_dir = repo_root.resolve()
    resources: list[CaseResource] = []
    entries = [
        ("demo_case_tree", "sanitized-case-tree.txt"),
        ("demo_verification_summary", "sanitized-verification-summary.txt"),
        ("demo_operator_brief", "sanitized-operator-brief.md"),
    ]
    if include_ai_review:
        entries.append(("ai_triage_summary", "sanitized-ai-triage-summary.md"))
    for source_id, filename in entries:
        spec = _spec_for_resource(
            {
                "source_id": source_id,
                "kind": source_id,
                "artifact": (
                    DEMO_RESOURCE_SPECS.get(source_id)
                    or CASE_RESOURCE_SPECS[source_id]
                ).artifact,
            }
        )
        path = demo_dir / filename
        resource = _resource(
            source_id=spec.source_id,
            artifact=spec.artifact,
            path=path if path.exists() else None,
            root_dir=root_dir,
            content=_read_text(path if path.exists() else None, root_dir),
            kind=spec.kind,
        )
        if resource is not None:
            resources.append(resource)
    return resources


def build_case_resource_lookup(root_dir: Path, *, include_ai_review: bool = True) -> dict[str, CaseResource]:
    return {
        item.source_id: item for item in build_case_resources(root_dir, include_ai_review=include_ai_review)
    }


def describe_case_resources(resources: Iterable[CaseResource]) -> list[dict[str, Any]]:
    described: list[dict[str, Any]] = []
    for item in resources:
        spec = _spec_for_resource(item)
        described.append(
            {
                "source_id": item.source_id,
                "artifact": item.artifact,
                "relpath": item.relpath,
                "kind": item.kind,
                "tier": spec.tier,
            }
        )
    return described


def summarize_case_root(root_dir: Path, *, include_ai_review: bool = True) -> dict[str, Any]:
    root_dir = root_dir.expanduser().resolve()
    resources = build_case_resources(root_dir, include_ai_review=include_ai_review)
    resource_paths = {item.source_id: item.relpath for item in resources}
    return {
        "retrieval_contract_version": DERIVED_ARTIFACT_RETRIEVAL_CONTRACT_VERSION,
        "primary_retrieval_unit": PRIMARY_RETRIEVAL_UNIT,
        "case_root_name": root_dir.name,
        "case_root": str(root_dir),
        "resource_count": len(resources),
        "resources": resource_paths,
        "resource_items": describe_case_resources(resources),
    }


def tokenize_query(query: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(query)]
    seen: set[str] = set()
    unique_tokens: list[str] = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        unique_tokens.append(token)
    return unique_tokens


def search_case_resources(
    resources: Iterable[CaseResource],
    query: str,
    *,
    max_results: int = 6,
) -> list[dict[str, Any]]:
    resource_list = list(resources)
    tokens = tokenize_query(query)
    scored: list[tuple[float, CaseResource]] = []
    for item in resource_list:
        base_weight = RESOURCE_WEIGHTS.get(item.kind, 1.0)
        lowered = item.content.lower()
        token_hits = sum(lowered.count(token) for token in tokens)
        if tokens:
            score = token_hits * base_weight
        else:
            score = base_weight
        if score <= 0 and tokens:
            continue
        scored.append((score, item))
    if not scored:
        scored = [(RESOURCE_WEIGHTS.get(item.kind, 1.0), item) for item in resource_list]
    scored.sort(key=lambda pair: (pair[0], RESOURCE_WEIGHTS.get(pair[1].kind, 1.0)), reverse=True)
    results: list[dict[str, Any]] = []
    for score, item in scored[:max_results]:
        spec = _spec_for_resource(item)
        results.append(
            {
                "source_id": item.source_id,
                "artifact": item.artifact,
                "path": item.relpath,
                "relpath": item.relpath,
                "kind": item.kind,
                "tier": spec.tier,
                "excerpt": item.excerpt,
                "score": round(float(score), 2),
            }
        )
    return results


def select_case_evidence(
    resources: Iterable[CaseResource],
    query: str,
    *,
    max_results: int = 6,
) -> list[dict[str, Any]]:
    resource_list = list(resources)
    query_tokens = tokenize_query(query)
    matched_ids: set[str] = set()
    if query_tokens:
        for item in resource_list:
            lowered = item.content.lower()
            if any(token in lowered for token in query_tokens):
                matched_ids.add(item.source_id)
    ranked_items = search_case_resources(resource_list, query, max_results=max_results)
    ranked_index = {item["source_id"]: item for item in ranked_items}
    all_items = {
        item.source_id: {
            "source_id": item.source_id,
            "artifact": item.artifact,
            "path": item.relpath,
            "relpath": item.relpath,
            "kind": item.kind,
            "tier": _spec_for_resource(item).tier,
            "excerpt": item.excerpt,
            "score": 0.0,
        }
        for item in resource_list
    }

    selected_ids: list[str] = []
    injected_ids: set[str] = set()
    for source_id in DEFAULT_TIER_A_SOURCE_IDS:
        if source_id in all_items and source_id not in selected_ids:
            selected_ids.append(source_id)
            injected_ids.add(source_id)
    for source_id in DEFAULT_TIER_B_SOURCE_IDS:
        if source_id in all_items and source_id not in selected_ids and len(selected_ids) < max_results:
            selected_ids.append(source_id)
            injected_ids.add(source_id)
    for item in ranked_items:
        if item["source_id"] not in selected_ids and len(selected_ids) < max_results:
            selected_ids.append(item["source_id"])

    selected: list[dict[str, Any]] = []
    for source_id in selected_ids[:max_results]:
        base = dict(all_items[source_id])
        matched = source_id in matched_ids
        if matched:
            base["score"] = ranked_index[source_id]["score"]
        base["selection_reason"] = _selection_reason(
            base,
            matched=matched,
            injected=source_id in injected_ids,
        )
        base["locator"] = None
        selected.append(base)
    return selected


def build_evidence_ref(
    item: dict[str, Any],
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    resolved_reason = (reason or "").strip() or str(item["selection_reason"])
    return {
        "source_id": item["source_id"],
        "artifact": item["artifact"],
        "path": item["path"],
        "relpath": item["relpath"],
        "kind": item["kind"],
        "selection_reason": resolved_reason,
        "score": item["score"],
        "locator": item["locator"],
        "reason": resolved_reason,
        "excerpt": item["excerpt"],
    }


def build_suggested_target(
    item: dict[str, Any],
    *,
    reason: str | None = None,
) -> dict[str, str]:
    resolved_reason = (reason or "").strip() or str(item["selection_reason"])
    return {
        "artifact": item["artifact"],
        "path": item["path"],
        "relpath": item["relpath"],
        "reason": resolved_reason,
    }


def build_artifact_priority_items(
    evidence_items: Iterable[dict[str, Any]],
    *,
    max_results: int = 4,
) -> list[dict[str, Any]]:
    priorities: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in evidence_items:
        source_id = str(item["source_id"])
        if source_id in seen:
            continue
        seen.add(source_id)
        priorities.append(
            {
                "artifact": str(item["artifact"]),
                "priority": len(priorities) + 1,
                "reason": str(item["selection_reason"]),
                "source_id": source_id,
                "tier": str(item["tier"]),
                "relpath": str(item["relpath"]),
                "kind": str(item["kind"]),
                "selection_reason": str(item["selection_reason"]),
            }
        )
        if len(priorities) >= max_results:
            break
    return priorities


def normalize_artifact_priority_items(
    raw_items: Iterable[dict[str, Any]],
    evidence_items: Iterable[dict[str, Any]],
    *,
    max_results: int = 4,
) -> list[dict[str, Any]]:
    evidence_list = list(evidence_items)
    if not evidence_list:
        return []

    evidence_by_source_id = {
        str(item["source_id"]): item for item in evidence_list if item.get("source_id")
    }
    evidence_by_source_id_lower = {
        source_id.lower(): item for source_id, item in evidence_by_source_id.items()
    }
    evidence_by_artifact = {
        str(item["artifact"]).strip().lower(): item
        for item in evidence_list
        if str(item.get("artifact", "")).strip()
    }

    priorities: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("source_id", "")).strip()
        artifact = str(item.get("artifact", "")).strip()
        reason = str(item.get("reason", "")).strip()
        priority_raw = item.get("priority", len(priorities) + 1)
        try:
            priority = int(priority_raw)
        except (TypeError, ValueError):
            priority = len(priorities) + 1

        matched = None
        if source_id and source_id in evidence_by_source_id:
            matched = evidence_by_source_id[source_id]
        elif source_id and source_id.lower() in evidence_by_source_id_lower:
            matched = evidence_by_source_id_lower[source_id.lower()]
        elif artifact and artifact in evidence_by_source_id:
            matched = evidence_by_source_id[artifact]
        elif artifact and artifact.lower() in evidence_by_source_id_lower:
            matched = evidence_by_source_id_lower[artifact.lower()]
        elif artifact and artifact.lower() in evidence_by_artifact:
            matched = evidence_by_artifact[artifact.lower()]

        if matched is None:
            dedupe_key = source_id or artifact or f"artifact_priority_{index}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            priorities.append(
                {
                    "artifact": artifact or "unknown",
                    "priority": priority,
                    "reason": reason or "No reason provided.",
                    "source_id": source_id,
                }
            )
        else:
            canonical_source_id = str(matched["source_id"])
            if canonical_source_id in seen:
                continue
            seen.add(canonical_source_id)
            resolved_reason = reason or str(matched["selection_reason"])
            priorities.append(
                {
                    "artifact": str(matched["artifact"]),
                    "priority": priority,
                    "reason": resolved_reason,
                    "source_id": canonical_source_id,
                    "tier": str(matched["tier"]),
                    "relpath": str(matched["relpath"]),
                    "kind": str(matched["kind"]),
                    "selection_reason": resolved_reason,
                }
            )
        if len(priorities) >= max_results:
            break

    if priorities:
        priorities.sort(key=lambda item: int(item["priority"]))
        return priorities[:max_results]

    return build_artifact_priority_items(evidence_list, max_results=max_results)


def inspect_case_resource(
    root_dir: Path,
    source_id: str,
    *,
    include_ai_review: bool = True,
) -> dict[str, Any]:
    lookup = build_case_resource_lookup(root_dir, include_ai_review=include_ai_review)
    if source_id not in lookup:
        raise KeyError(source_id)
    resource = lookup[source_id]
    spec = _spec_for_resource(resource)
    return {
        "source_id": resource.source_id,
        "artifact": resource.artifact,
        "relpath": resource.relpath,
        "kind": resource.kind,
        "tier": spec.tier,
        "mode": spec.mode,
        "selection_reason": spec.default_selection_reason,
        "excerpt": resource.excerpt,
        "content": resource.content,
        "retrieval_contract_version": DERIVED_ARTIFACT_RETRIEVAL_CONTRACT_VERSION,
        "primary_retrieval_unit": PRIMARY_RETRIEVAL_UNIT,
    }


def default_case_search_roots() -> list[Path]:
    return [config.DEFAULT_OUTPUT_ROOT.parent]
