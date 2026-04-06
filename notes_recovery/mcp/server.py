from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

import notes_recovery.config as config
from notes_recovery.cli.analysis_handlers import handle_timeline_command
from notes_recovery.cli.tail_handlers import (
    handle_public_safe_export_command,
    handle_report_command,
    handle_verify_command,
)
from notes_recovery.core.pipeline import (
    assert_pipeline_ok,
    build_timestamped_dir,
    build_timestamped_file,
    finalize_pipeline,
    run_pipeline,
    timestamp_now,
)
from notes_recovery.core.text_bundle import generate_text_bundle
from notes_recovery.io import resolve_path
from notes_recovery.services.ask_case import run_ask_case
from notes_recovery.services.case_protocol import (
    build_evidence_ref,
    build_case_resource_lookup,
    build_demo_resources,
    derived_artifact_retrieval_contract,
    default_case_search_roots,
    discover_case_roots,
    inspect_case_resource,
    select_case_evidence,
    summarize_case_root,
)
from notes_recovery.services.public_safe import public_safe_export
from notes_recovery.services.report import generate_report
from notes_recovery.services.timeline import build_timeline
from notes_recovery.services.verify import verify_hits

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations
except ModuleNotFoundError as exc:  # pragma: no cover - exercised in runtime usage
    raise SystemExit(
        "The MCP server requires the optional MCP dependencies. Install `python -m pip install -e .[mcp]` first."
    ) from exc


CASE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")
DEMO_RESOURCE_MAP = {
    "case-tree": "demo_case_tree",
    "verification-summary": "demo_verification_summary",
    "operator-brief": "demo_operator_brief",
    "ai-triage-summary": "ai_triage_summary",
}


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    root_dir: Path


class CaseRegistry:
    def __init__(self, records: list[CaseRecord]) -> None:
        self._records = {record.case_id: record for record in records}

    @classmethod
    def build(cls, case_dirs: Iterable[Path], cases_roots: Iterable[Path]) -> "CaseRegistry":
        roots = discover_case_roots(case_dirs=case_dirs, search_roots=cases_roots)
        name_counts: dict[str, int] = {}
        for root in roots:
            name_counts[root.name] = name_counts.get(root.name, 0) + 1
        records: list[CaseRecord] = []
        for root in roots:
            safe_name = CASE_ID_RE.sub("-", root.name).strip("-") or "case"
            if name_counts[root.name] > 1:
                digest = hashlib.sha1(str(root).encode("utf-8")).hexdigest()[:8]
                case_id = f"{safe_name}--{digest}"
            else:
                case_id = safe_name
            records.append(CaseRecord(case_id=case_id, root_dir=root))
        return cls(records)

    def list(self) -> list[CaseRecord]:
        return sorted(self._records.values(), key=lambda item: item.case_id)

    def require(self, case_id: str) -> CaseRecord:
        record = self._records.get(case_id)
        if record is None:
            raise ValueError(f"Unknown case id: {case_id}")
        return record


def _quiet_logging(*_args: Any, **_kwargs: Any) -> None:
    return None


def _run_quietly(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return func(*args, **kwargs)


def _read_resource_text(case_root: Path, source_id: str) -> str:
    lookup = build_case_resource_lookup(case_root, include_ai_review=True)
    if source_id not in lookup:
        raise ValueError(f"Resource is not available for this case: {source_id}")
    return lookup[source_id].content


def build_mcp_server(
    *,
    repo_root: Path,
    case_dirs: Iterable[Path],
    cases_roots: Iterable[Path],
) -> FastMCP:
    registry = CaseRegistry.build(case_dirs, cases_roots)
    retrieval_contract = derived_artifact_retrieval_contract()
    server = FastMCP(
        "NoteStore Lab MCP",
        instructions=(
            "Read-mostly MCP server for copy-first Apple Notes recovery cases. "
            "Stay on derived review artifacts and bounded derived-output tools."
        ),
    )

    read_only = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    bounded_write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )

    @server.resource(
        "case://{case_id}/run-manifest",
        name="case_run_manifest",
        mime_type="application/json",
    )
    def case_run_manifest(case_id: str) -> str:
        return _read_resource_text(registry.require(case_id).root_dir, "run_manifest")

    @server.resource(
        "case://{case_id}/case-manifest",
        name="case_case_manifest",
        mime_type="application/json",
    )
    def case_case_manifest(case_id: str) -> str:
        return _read_resource_text(registry.require(case_id).root_dir, "case_manifest")

    @server.resource(
        "case://{case_id}/pipeline-summary",
        name="case_pipeline_summary",
        mime_type="text/markdown",
    )
    def case_pipeline_summary(case_id: str) -> str:
        return _read_resource_text(registry.require(case_id).root_dir, "pipeline_summary")

    @server.resource(
        "case://{case_id}/review-index",
        name="case_review_index",
        mime_type="text/markdown",
    )
    def case_review_index(case_id: str) -> str:
        return _read_resource_text(registry.require(case_id).root_dir, "review_index")

    @server.resource(
        "case://{case_id}/verification-summary",
        name="case_verification_summary",
        mime_type="text/plain",
    )
    def case_verification_summary(case_id: str) -> str:
        return _read_resource_text(registry.require(case_id).root_dir, "verification_preview")

    @server.resource(
        "case://{case_id}/timeline-summary",
        name="case_timeline_summary",
        mime_type="application/json",
    )
    def case_timeline_summary(case_id: str) -> str:
        return _read_resource_text(registry.require(case_id).root_dir, "timeline_summary")

    @server.resource(
        "case://{case_id}/ai-triage-summary",
        name="case_ai_triage_summary",
        mime_type="text/markdown",
    )
    def case_ai_triage_summary(case_id: str) -> str:
        return _read_resource_text(registry.require(case_id).root_dir, "ai_triage_summary")

    @server.resource(
        "demo://public-safe/{name}",
        name="demo_public_safe",
        mime_type="text/plain",
    )
    def demo_public_safe(name: str) -> str:
        key = DEMO_RESOURCE_MAP.get(name)
        if key is None:
            raise ValueError(f"Unknown demo resource: {name}")
        resources = {item.source_id: item for item in build_demo_resources(repo_root)}
        if key not in resources:
            raise ValueError(f"Demo resource is not available: {name}")
        return resources[key].content

    @server.tool(
        name="list_case_roots",
        description="List the allowed case roots that this MCP server can inspect.",
        annotations=read_only,
    )
    def list_case_roots() -> dict[str, Any]:
        cases = []
        for record in registry.list():
            summary = summarize_case_root(record.root_dir, include_ai_review=True)
            cases.append(
                {
                    "case_id": record.case_id,
                    "case_root_name": record.root_dir.name,
                    "resource_count": summary["resource_count"],
                    "resources": summary["resources"],
                    "retrieval_contract_version": summary["retrieval_contract_version"],
                }
            )
        return {
            "cases": cases,
            "retrieval_contract_version": retrieval_contract["version"],
            "primary_retrieval_unit": retrieval_contract["primary_retrieval_unit"],
        }

    @server.tool(
        name="inspect_case_manifest",
        description="Return a structured summary of one case root and its current derived resources.",
        annotations=read_only,
    )
    def inspect_case_manifest(case_id: str) -> dict[str, Any]:
        record = registry.require(case_id)
        summary = summarize_case_root(record.root_dir, include_ai_review=True)
        summary["retrieval_contract"] = retrieval_contract
        return summary

    @server.tool(
        name="select_case_evidence",
        description="Return the shared selector output for one case root and question using the retrieval contract SSOT.",
        annotations=read_only,
    )
    def select_case_evidence_tool(
        case_id: str,
        question: str,
        max_results: int = 6,
    ) -> dict[str, Any]:
        record = registry.require(case_id)
        resources = list(
            build_case_resource_lookup(record.root_dir, include_ai_review=True).values()
        )
        evidence_items = select_case_evidence(
            resources,
            question,
            max_results=max_results,
        )
        return {
            "case_id": case_id,
            "question": question,
            "retrieval_contract_version": retrieval_contract["version"],
            "primary_retrieval_unit": retrieval_contract["primary_retrieval_unit"],
            "evidence_ref_schema_version": retrieval_contract[
                "evidence_ref_schema_version"
            ],
            "evidence_refs": [build_evidence_ref(item) for item in evidence_items],
        }

    @server.tool(
        name="inspect_case_artifact",
        description="Return one contract-backed derived artifact, including its tier, excerpt, and bounded content.",
        annotations=read_only,
    )
    def inspect_case_artifact(case_id: str, source_id: str) -> dict[str, Any]:
        record = registry.require(case_id)
        payload = inspect_case_resource(
            record.root_dir,
            source_id,
            include_ai_review=True,
        )
        payload["case_id"] = case_id
        return payload

    @server.tool(
        name="inspect_run_manifest",
        description="Return the latest run manifest payload for a case root.",
        annotations=read_only,
    )
    def inspect_run_manifest(case_id: str) -> dict[str, Any]:
        record = registry.require(case_id)
        text = _read_resource_text(record.root_dir, "run_manifest")
        return json.loads(text)

    @server.tool(
        name="ask_case",
        description="Ask an evidence-backed question about one case root using derived review artifacts.",
        annotations=read_only,
    )
    def ask_case(
        case_id: str,
        question: str,
        provider: str | None = None,
        model: str | None = None,
        allow_cloud: bool = False,
    ) -> dict[str, Any]:
        record = registry.require(case_id)
        return run_ask_case(
            root_dir=record.root_dir,
            question=question,
            demo=False,
            repo_root=repo_root,
            provider=provider,
            model=model,
            allow_cloud=allow_cloud,
        )

    @server.tool(
        name="run_verify",
        description="Run the bounded verify workflow against a case root and return the newest verification outputs.",
        annotations=bounded_write,
    )
    def run_verify(
        case_id: str,
        keyword: str,
        top_n: int = 10,
        preview_len: int = 300,
    ) -> dict[str, Any]:
        record = registry.require(case_id)
        args = SimpleNamespace(
            dir=str(record.root_dir),
            out=None,
            keyword=keyword,
            top=top_n,
            preview_len=preview_len,
            no_deep=False,
            deep_max_mb=0,
            deep_max_hits_per_file=200,
            deep_core_only=False,
            match_all=False,
            no_fuzzy=False,
            fuzzy_threshold=0.72,
            fuzzy_boost=6.0,
            fuzzy_max_len=2000,
        )
        exit_code = _run_quietly(
            handle_verify_command,
            args,
            resolve_path=resolve_path,
            timestamp_now=timestamp_now,
            build_timestamped_dir=build_timestamped_dir,
            setup_cli_logging=_quiet_logging,
            verify_hits=verify_hits,
            generate_text_bundle=generate_text_bundle,
            run_pipeline=run_pipeline,
            finalize_pipeline=finalize_pipeline,
            assert_pipeline_ok=assert_pipeline_ok,
        )
        if exit_code != 0:
            raise RuntimeError("Verify command failed from MCP.")
        summary = summarize_case_root(record.root_dir, include_ai_review=True)
        return {"exit_code": exit_code, "case_id": case_id, "resources": summary["resources"]}

    @server.tool(
        name="run_report",
        description="Run the bounded report workflow against a case root and return the newest report/text-bundle outputs.",
        annotations=bounded_write,
    )
    def run_report(
        case_id: str,
        keyword: str | None = None,
        max_items: int = 50,
    ) -> dict[str, Any]:
        record = registry.require(case_id)
        args = SimpleNamespace(
            dir=str(record.root_dir),
            out=None,
            keyword=keyword,
            max_items=max_items,
        )
        exit_code = _run_quietly(
            handle_report_command,
            args,
            resolve_path=resolve_path,
            timestamp_now=timestamp_now,
            build_timestamped_file=build_timestamped_file,
            setup_cli_logging=_quiet_logging,
            generate_report=generate_report,
            generate_text_bundle=generate_text_bundle,
            run_pipeline=run_pipeline,
            finalize_pipeline=finalize_pipeline,
            assert_pipeline_ok=assert_pipeline_ok,
        )
        if exit_code != 0:
            raise RuntimeError("Report command failed from MCP.")
        summary = summarize_case_root(record.root_dir, include_ai_review=True)
        return {"exit_code": exit_code, "case_id": case_id, "resources": summary["resources"]}

    @server.tool(
        name="build_timeline",
        description="Build the bounded timeline workflow against a case root and return the newest timeline outputs.",
        annotations=bounded_write,
    )
    def build_timeline_tool(
        case_id: str,
        keyword: str | None = None,
        max_notes: int = 200,
        max_events: int = 2000,
        spotlight_max_files: int = 100,
    ) -> dict[str, Any]:
        record = registry.require(case_id)
        args = SimpleNamespace(
            dir=str(record.root_dir),
            out=None,
            keyword=keyword,
            max_notes=max_notes,
            max_events=max_events,
            spotlight_max_files=spotlight_max_files,
            no_fs=False,
            no_plotly=True,
        )
        exit_code = _run_quietly(
            handle_timeline_command,
            args,
            resolve_path=resolve_path,
            timestamp_now=timestamp_now,
            build_timestamped_dir=build_timestamped_dir,
            setup_cli_logging=_quiet_logging,
            build_timeline=build_timeline,
            generate_text_bundle=generate_text_bundle,
            run_pipeline=run_pipeline,
            finalize_pipeline=finalize_pipeline,
            assert_pipeline_ok=assert_pipeline_ok,
            timeline_strategy_version=config.TIMELINE_STRATEGY_VERSION,
        )
        if exit_code != 0:
            raise RuntimeError("Timeline command failed from MCP.")
        summary = summarize_case_root(record.root_dir, include_ai_review=True)
        return {"exit_code": exit_code, "case_id": case_id, "resources": summary["resources"]}

    @server.tool(
        name="public_safe_export",
        description="Create a redacted public-safe bundle for one case root.",
        annotations=bounded_write,
    )
    def public_safe_export_tool(case_id: str, out_dir: str | None = None) -> dict[str, Any]:
        record = registry.require(case_id)
        if out_dir is None:
            out_value = f"./output/public_safe_bundle_{case_id}"
        else:
            candidate = Path(out_dir)
            if candidate.is_absolute():
                raise ValueError("MCP public_safe_export only accepts a relative output directory.")
            out_value = out_dir
        args = SimpleNamespace(dir=str(record.root_dir), out=out_value)
        exit_code = _run_quietly(
            handle_public_safe_export_command,
            args,
            resolve_path=resolve_path,
            timestamp_now=timestamp_now,
            build_timestamped_dir=build_timestamped_dir,
            setup_cli_logging=_quiet_logging,
            public_safe_export=public_safe_export,
            run_pipeline=run_pipeline,
            assert_pipeline_ok=assert_pipeline_ok,
        )
        if exit_code != 0:
            raise RuntimeError("public-safe-export command failed from MCP.")
        out_root = resolve_path(out_value).parent
        latest = sorted(out_root.glob(f"{Path(out_value).name}_*"))
        latest_dir = latest[-1] if latest else None
        return {
            "exit_code": exit_code,
            "case_id": case_id,
            "public_safe_dir": str(latest_dir) if latest_dir else "",
        }

    return server


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notes-recovery-mcp",
        description="Read-mostly MCP server for copy-first Apple Notes recovery cases.",
    )
    parser.add_argument(
        "--case-dir",
        action="append",
        default=[],
        help="Explicit case root to expose (repeatable).",
    )
    parser.add_argument(
        "--cases-root",
        action="append",
        default=[],
        help="Parent directory to scan for case roots (repeatable). Defaults to ./output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    case_dirs = [Path(item) for item in args.case_dir]
    cases_roots = [Path(item) for item in args.cases_root] or default_case_search_roots()
    server = build_mcp_server(repo_root=repo_root, case_dirs=case_dirs, cases_roots=cases_roots)
    server.run("stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
