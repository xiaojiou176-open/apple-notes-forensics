from __future__ import annotations

import sys
from pathlib import Path

try:
    from scripts.ci.contracts import (
        BASELINE_DEMO_COMMAND,
        BASELINE_DOC_COMMAND,
        BASELINE_TESTS,
        FULL_SUITE_DOC_COMMAND,
        README_VERIFICATION_REQUIRED_TOKENS,
        VERIFICATION_SUMMARY_TOKENS,
        WORKFLOW_DEMO_COMMAND,
        WORKFLOW_HELP_COMMAND,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from contracts import (
        BASELINE_DEMO_COMMAND,
        BASELINE_DOC_COMMAND,
        BASELINE_TESTS,
        FULL_SUITE_DOC_COMMAND,
        README_VERIFICATION_REQUIRED_TOKENS,
        VERIFICATION_SUMMARY_TOKENS,
        WORKFLOW_DEMO_COMMAND,
        WORKFLOW_HELP_COMMAND,
    )


DOC_FILES = (
    "README.md",
    "CONTRIBUTING.md",
)

FORBIDDEN_BASELINE_LINES = (
    ".venv/bin/python -m pytest tests/",
    "python -m pytest tests/",
)


def _read(repo_root: Path, rel_path: str) -> str | None:
    path = repo_root / rel_path
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def collect_verification_contract_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []

    workflow_text = _read(repo_root, ".github/workflows/ci.yml")
    if workflow_text is None:
        return ["missing .github/workflows/ci.yml"]

    if WORKFLOW_HELP_COMMAND not in workflow_text:
        errors.append("workflow baseline is missing the CLI help command")
    if WORKFLOW_DEMO_COMMAND not in workflow_text:
        errors.append("workflow baseline is missing the public demo command")

    for test_path in BASELINE_TESTS:
        if test_path not in workflow_text:
            errors.append(f"workflow baseline is missing canonical smoke test: {test_path}")

    readme_text = _read(repo_root, "README.md")
    if readme_text is None:
        errors.append("missing verification contract doc: README.md")
    else:
        lowered = readme_text.casefold()
        stripped_lines = {line.strip() for line in readme_text.splitlines()}
        for token in README_VERIFICATION_REQUIRED_TOKENS:
            if token.casefold() not in lowered:
                errors.append(f"README.md is missing verification contract token: {token}")
        for forbidden in FORBIDDEN_BASELINE_LINES:
            if forbidden in stripped_lines:
                errors.append(f"README.md must not claim `{forbidden}` as the baseline contract")
        for test_path in BASELINE_TESTS:
            if test_path in readme_text:
                errors.append(f"README.md must keep canonical smoke test paths in CONTRIBUTING.md only: {test_path}")

    contributing_text = _read(repo_root, "CONTRIBUTING.md")
    if contributing_text is None:
        errors.append("missing verification contract doc: CONTRIBUTING.md")
    else:
        lowered = contributing_text.casefold()
        stripped_lines = {line.strip() for line in contributing_text.splitlines()}

        if BASELINE_DOC_COMMAND not in contributing_text:
            errors.append("CONTRIBUTING.md is missing the canonical baseline help command")
        if BASELINE_DEMO_COMMAND not in contributing_text:
            errors.append("CONTRIBUTING.md is missing the canonical public demo command")

        for forbidden in FORBIDDEN_BASELINE_LINES:
            if forbidden in stripped_lines:
                errors.append(f"CONTRIBUTING.md must not claim `{forbidden}` as the baseline contract")

        for token in VERIFICATION_SUMMARY_TOKENS:
            if token not in lowered:
                errors.append(f"CONTRIBUTING.md is missing verification contract token: {token}")

        for test_path in BASELINE_TESTS:
            if test_path not in contributing_text:
                errors.append(f"CONTRIBUTING.md is missing canonical smoke test: {test_path}")
        if FULL_SUITE_DOC_COMMAND not in contributing_text:
            errors.append("CONTRIBUTING.md should document the broader full suite sweep explicitly")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    errors = collect_verification_contract_errors(repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("verification contract check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
