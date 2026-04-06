from __future__ import annotations

from pathlib import Path
import traceback
from typing import Any

from notes_recovery.case_contract import (
    CASE_DIR_RECOVERED_BLOBS,
    CASE_DIR_RECOVERED_DB,
    case_dir,
)
from notes_recovery.services.auto import auto_run
from notes_recovery.services.carve import carve_gzip, normalize_carve_algorithms
from notes_recovery.services.fsevents import correlate_fsevents_with_spotlight
from notes_recovery.services.freelist import freelist_carve
from notes_recovery.services.flatten import flatten_backup
from notes_recovery.services.fts import build_fts_index
from notes_recovery.services.gui import run_gui
from notes_recovery.services.plugins import run_plugins
from notes_recovery.services.plugins import validate_plugins_config
from notes_recovery.services.plugins import render_plugins_validation_report
from notes_recovery.services.protobuf import parse_notes_protobuf
from notes_recovery.services.public_safe import public_safe_export
from notes_recovery.services.doctor import run_doctor
from notes_recovery.services.ai_review import run_ai_review
from notes_recovery.services.ask_case import run_ask_case
from notes_recovery.services.case_diff import build_case_diff_payload, write_case_diff_outputs
from notes_recovery.services.query import query_notes
from notes_recovery.services.recover import recover_notes_by_keyword, sqlite_recover
from notes_recovery.services.report import generate_report
from notes_recovery.services.snapshot import snapshot
from notes_recovery.services.spotlight import parse_spotlight_deep
from notes_recovery.services.timeline import build_timeline
from notes_recovery.services.verify import verify_hits
from notes_recovery.services.wal import wal_diff, wal_extract, wal_isolate
from notes_recovery.services.wizard import run_wizard
from notes_recovery.cli.analysis_handlers import (
    handle_protobuf_command,
    handle_query_command,
    handle_spotlight_parse_command,
    handle_timeline_command,
)
from notes_recovery.cli.evidence_handlers import (
    handle_freelist_command,
    handle_fsevents_command,
    handle_fts_command,
    handle_snapshot_command,
    handle_wal_diff_command,
    handle_wal_extract_command,
    handle_wal_isolate_command,
)
from notes_recovery.cli.orchestration_handlers import (
    handle_auto_command,
    handle_flatten_command,
    handle_plugins_command,
)
from notes_recovery.config import DEFAULT_OUTPUT_ROOT, SPOTLIGHT_PARSE_STRATEGY_VERSION, TIMELINE_STRATEGY_VERSION
from notes_recovery.cli.tail_handlers import (
    handle_demo_command,
    handle_doctor_command,
    handle_ai_review_command,
    handle_ask_case_command,
    handle_plugins_validate_command,
    handle_case_diff_command,
    handle_public_safe_export_command,
    handle_gui_command,
    handle_recover_notes_command,
    handle_report_command,
    handle_verify_command,
    handle_wizard_command,
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
from notes_recovery.logging import LOG_CONTEXT, LOG_LEVELS, eprint, setup_cli_logging
from notes_recovery.models import ExitCode, PipelineStage


def run_command(args) -> int:
    try:
        if args.command == "ai-review":
            return handle_ai_review_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                run_ai_review=run_ai_review,
            )

        if args.command == "ask-case":
            return handle_ask_case_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                setup_cli_logging=setup_cli_logging,
                run_ask_case=run_ask_case,
            )

        if args.command == "doctor":
            return handle_doctor_command(
                args,
                timestamp_now=timestamp_now,
                setup_cli_logging=setup_cli_logging,
                run_doctor=run_doctor,
            )

        if args.command == "plugins-validate":
            return handle_plugins_validate_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                setup_cli_logging=setup_cli_logging,
                validate_plugins_config=validate_plugins_config,
                render_plugins_validation_report=render_plugins_validation_report,
            )

        if args.command == "case-diff":
            return handle_case_diff_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                build_case_diff_payload=build_case_diff_payload,
                write_case_diff_outputs=write_case_diff_outputs,
            )

        if args.command == "snapshot":
            return handle_snapshot_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                snapshot=snapshot,
                flatten_backup=flatten_backup,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )

        if args.command == "wal-isolate":
            return handle_wal_isolate_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                setup_cli_logging=setup_cli_logging,
                wal_isolate=wal_isolate,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )

        if args.command == "wal-extract":
            return handle_wal_extract_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                wal_extract=wal_extract,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )

        if args.command == "wal-diff":
            return handle_wal_diff_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                wal_diff=wal_diff,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )

        if args.command == "freelist-carve":
            return handle_freelist_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                freelist_carve=freelist_carve,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )

        if args.command == "fsevents-correlate":
            return handle_fsevents_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                correlate_fsevents_with_spotlight=correlate_fsevents_with_spotlight,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )

        if args.command == "fts-index":
            return handle_fts_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                build_fts_index=build_fts_index,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )

        if args.command == "query":
            return handle_query_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                query_notes=query_notes,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
                default_output_root=str(DEFAULT_OUTPUT_ROOT),
            )
        if args.command == "protobuf":
            return handle_protobuf_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                parse_notes_protobuf=parse_notes_protobuf,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
                default_output_root=str(DEFAULT_OUTPUT_ROOT),
            )

        if args.command == "timeline":
            return handle_timeline_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                build_timeline=build_timeline,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
                timeline_strategy_version=TIMELINE_STRATEGY_VERSION,
            )

        if args.command == "spotlight-parse":
            return handle_spotlight_parse_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                parse_spotlight_deep=parse_spotlight_deep,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
                spotlight_strategy_version=SPOTLIGHT_PARSE_STRATEGY_VERSION,
            )

        if args.command == "carve-gzip":
            run_ts = timestamp_now()
            if args.out:
                base_out = resolve_path(args.out)
                out_dir = build_timestamped_dir(base_out, run_ts)
                run_root = out_dir
            else:
                run_root = build_timestamped_dir(resolve_path(str(DEFAULT_OUTPUT_ROOT)), run_ts)
                out_dir = case_dir(run_root, CASE_DIR_RECOVERED_BLOBS)
            setup_cli_logging(args, run_ts, run_root, "carve-gzip")
            print(f"Timestamped output directory: {out_dir}")
            db_path = resolve_path(args.db)

            def stage_carve() -> dict[str, Any]:
                carve_gzip(
                    db_path,
                    out_dir,
                    args.keyword,
                    args.max_hits,
                    args.window_size,
                    args.min_text_len,
                    args.min_text_ratio,
                    normalize_carve_algorithms(args.algorithms),
                    args.max_output_mb,
                )
                return {"db_path": str(db_path), "carve_dir": str(out_dir)}

            def stage_bundle() -> dict[str, Any]:
                return {"bundle_root": str(generate_text_bundle(out_dir, run_ts, args.keyword))}

            stages = [
                PipelineStage("carve-gzip", True, True, stage_carve),
                PipelineStage("text-bundle", True, True, stage_bundle),
            ]
            stage_results = run_pipeline(stages)
            config = {
                "db_path": str(db_path),
                "keyword": args.keyword,
                "max_hits": args.max_hits,
                "window_size": args.window_size,
                "min_text_len": args.min_text_len,
                "min_text_ratio": args.min_text_ratio,
                "out_dir": str(out_dir),
            }
            finalize_pipeline(run_root, run_ts, "carve-gzip", config, stage_results)
            assert_pipeline_ok(stage_results)
            return ExitCode.OK.value
        if args.command == "recover":
            run_ts = timestamp_now()
            if args.out:
                base_out = resolve_path(args.out)
                out_dir = build_timestamped_dir(base_out, run_ts)
                run_root = out_dir
            else:
                run_root = build_timestamped_dir(resolve_path(str(DEFAULT_OUTPUT_ROOT)), run_ts)
                out_dir = case_dir(run_root, CASE_DIR_RECOVERED_DB)
            setup_cli_logging(args, run_ts, run_root, "recover")
            print(f"Timestamped output directory: {out_dir}")
            db_path = resolve_path(args.db)

            def stage_recover() -> dict[str, Any]:
                sqlite_recover(
                    db_path,
                    out_dir,
                    args.ignore_freelist,
                    args.lost_and_found,
                )
                return {"db_path": str(db_path), "recovered_dir": str(out_dir)}

            def stage_bundle() -> dict[str, Any]:
                return {"bundle_root": str(generate_text_bundle(out_dir, run_ts, None))}

            stages = [
                PipelineStage("recover", True, True, stage_recover),
                PipelineStage("text-bundle", True, True, stage_bundle),
            ]
            stage_results = run_pipeline(stages)
            config = {
                "db_path": str(db_path),
                "ignore_freelist": args.ignore_freelist,
                "lost_and_found": args.lost_and_found,
                "out_dir": str(out_dir),
            }
            finalize_pipeline(run_root, run_ts, "recover", config, stage_results)
            assert_pipeline_ok(stage_results)
            return ExitCode.OK.value
        if args.command == "plugins":
            return handle_plugins_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                setup_cli_logging=setup_cli_logging,
                run_plugins=run_plugins,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )
        if args.command == "flatten":
            return handle_flatten_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                flatten_backup=flatten_backup,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )
        if args.command == "auto":
            return handle_auto_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                auto_run=auto_run,
            )
        if args.command == "demo":
            return handle_demo_command(
                args,
                timestamp_now=timestamp_now,
                setup_cli_logging=setup_cli_logging,
                repo_root=Path(__file__).resolve().parents[2],
            )
        if args.command == "public-safe-export":
            return handle_public_safe_export_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                public_safe_export=public_safe_export,
                run_pipeline=run_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )
        if args.command == "report":
            return handle_report_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_file=build_timestamped_file,
                setup_cli_logging=setup_cli_logging,
                generate_report=generate_report,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )
        if args.command == "verify":
            return handle_verify_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                verify_hits=verify_hits,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )
        if args.command == "recover-notes":
            return handle_recover_notes_command(
                args,
                resolve_path=resolve_path,
                timestamp_now=timestamp_now,
                build_timestamped_dir=build_timestamped_dir,
                setup_cli_logging=setup_cli_logging,
                recover_notes_by_keyword=recover_notes_by_keyword,
                generate_text_bundle=generate_text_bundle,
                run_pipeline=run_pipeline,
                finalize_pipeline=finalize_pipeline,
                assert_pipeline_ok=assert_pipeline_ok,
            )
        if args.command == "wizard":
            return handle_wizard_command(
                args,
                timestamp_now=timestamp_now,
                setup_cli_logging=setup_cli_logging,
                run_wizard=run_wizard,
            )
        if args.command == "gui":
            return handle_gui_command(run_gui=run_gui)

        eprint("Unknown command")
        return ExitCode.ERROR.value

    except Exception as exc:
        if LOG_CONTEXT.level <= LOG_LEVELS["debug"]:
            eprint(traceback.format_exc())
        else:
            eprint(str(exc))
        return ExitCode.ERROR.value
