#!/usr/bin/env python3
"""
Python Project Checkup - repository audit script

Scans for:
- Placeholders (TODO/FIXME/WIP/NOT_IMPLEMENTED/MOCK/DUMMY/PLACEHOLDER)
- NotImplementedError, pass-only functions, empty except blocks
- Dummy endpoints/strings (/test, /sample, /mock)
- Integration red flags (localhost, http URLs, hardcoded API keys)
- Testing/linters presence (pytest, tests/, flake8/black/ruff)
- Logging vs print usage

Usage:
  python tools/project_checkup.py --path . --output text
  python tools/project_checkup.py --output json > checkup_report.json
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Iterable, Optional, Set


DEFAULT_IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    ".mypy_cache",
}

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bWIP\b",
    r"\bNOT_IMPLEMENTED\b",
    r"\bTEMP\b",
    r"\bMOCK\b",
    r"\bDUMMY\b",
    r"\bPLACEHOLDER\b",
]

DUMMY_ENDPOINT_PATTERNS = [
    r"/test\b",
    r"/sample\b",
    r"/mock\b",
]

INTEGRATION_RED_FLAGS = [
    r"http://localhost",
    r"http://127\.0\.0\.1",
    r"\bAPI_KEY\b\s*[=:]",
    r"\bSECRET\b\s*[=:]",
    r"\bTOKEN\b\s*[=:]",
]


@dataclass
class Finding:
    type: str
    file: str
    line: int
    message: str


@dataclass
class Summary:
    files_scanned: int
    findings_count: int
    categories: Dict[str, int]


def iter_python_files(root: str, ignore_dirs: Set[str]) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored dirs in-place
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def safe_read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def scan_placeholders(path: str, text: str) -> List[Finding]:
    findings: List[Finding] = []
    for pat in PLACEHOLDER_PATTERNS:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(Finding("placeholder", path, line, f"Matched: {m.group(0)}"))
    return findings


def scan_dummy_endpoints(path: str, text: str) -> List[Finding]:
    findings: List[Finding] = []
    for pat in DUMMY_ENDPOINT_PATTERNS:
        for m in re.finditer(pat, text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(Finding("dummy_endpoint", path, line, f"Endpoint: {m.group(0)}"))
    return findings


def scan_integration_red_flags(path: str, text: str) -> List[Finding]:
    findings: List[Finding] = []
    for pat in INTEGRATION_RED_FLAGS:
        for m in re.finditer(pat, text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(Finding("integration_red_flag", path, line, f"Matched: {m.group(0)}"))
    return findings


def scan_ast_patterns(path: str, text: str) -> List[Finding]:
    findings: List[Finding] = []
    try:
        tree = ast.parse(text, filename=path)
    except Exception:
        return findings

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            # pass-only function
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                findings.append(Finding("pass_function", path, node.lineno, f"Function '{node.name}' contains only pass"))
            # return None in function (likely placeholder)
            # Reduce noise for typical callback/event-style names
            cb_like = any(node.name.endswith(suf) for suf in (
                "Event", "event", "Changed", "changed", "Clicked", "clicked", "Pressed", "pressed",
                "Released", "released", "update", "on_", "_on_", "show", "close", "load", "save"
            )) or node.name.startswith("on_")
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and (sub.value is None or isinstance(sub.value, ast.Constant) and sub.value.value is None):
                    if not cb_like:
                        findings.append(Finding("return_none", path, sub.lineno, f"return None in '{node.name}'"))
            self.generic_visit(node)

        def visit_Raise(self, node: ast.Raise) -> None:
            # raise NotImplementedError
            exc = node.exc
            if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) and exc.func.id == "NotImplementedError":
                findings.append(Finding("not_implemented", path, node.lineno, "raise NotImplementedError"))
            self.generic_visit(node)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            # empty except: pass
            if all(isinstance(b, ast.Pass) for b in node.body):
                name = getattr(node.type, "id", "Exception") if node.type else ""
                findings.append(Finding("empty_except", path, node.lineno, f"except {name}: pass"))
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            # API key like variable assigned to literal string
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if targets and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                joined = ",".join(targets).upper()
                if any(k in joined for k in ("API_KEY", "SECRET", "TOKEN")):
                    findings.append(Finding("hardcoded_secret", path, node.lineno, f"Hardcoded secret-like var: {joined}"))
            self.generic_visit(node)

    Visitor().visit(tree)
    return findings


def scan_print_usage(path: str, text: str) -> List[Finding]:
    findings: List[Finding] = []
    # Ignore tests and files starting with test_
    base = os.path.basename(path)
    if os.path.sep + "tests" + os.path.sep in path or base.startswith("test_"):
        return findings
    for m in re.finditer(r"\bprint\s*\(", text):
        line = text.count("\n", 0, m.start()) + 1
        findings.append(Finding("print_usage", path, line, "print() used; prefer logging"))
    return findings


def repo_checks(root: str) -> Dict[str, bool]:
    reqs = os.path.exists(os.path.join(root, "requirements.txt")) or os.path.exists(os.path.join(root, "pyproject.toml"))
    has_tests = any(
        name.startswith("test_") and name.endswith(".py") for name in os.listdir(root)
        if os.path.isfile(os.path.join(root, name))
    ) or os.path.isdir(os.path.join(root, "tests"))
    # simple dependency presence check
    requirements_txt = safe_read_text(os.path.join(root, "requirements.txt"))
    linters = any(k in requirements_txt for k in ("flake8", "black", "ruff")) if requirements_txt else False
    pytest_present = "pytest" in requirements_txt if requirements_txt else False
    env_present = os.path.exists(os.path.join(root, ".env")) or os.path.exists(os.path.join(root, "env.example"))
    return {
        "has_requirements": reqs,
        "has_tests": has_tests,
        "linters_in_requirements": linters,
        "pytest_in_requirements": pytest_present,
        "env_or_example_present": env_present,
    }


def format_text(summary: Summary, findings: List[Finding], repo_meta: Dict[str, bool]) -> str:
    lines: List[str] = []
    lines.append(f"Files scanned: {summary.files_scanned}")
    lines.append(f"Findings: {summary.findings_count}")
    lines.append("Repository checks:")
    for k, v in repo_meta.items():
        lines.append(f"  - {k}: {'OK' if v else 'MISSING'}")
    lines.append("")
    # Group findings by type
    by_type: Dict[str, List[Finding]] = {}
    for f in findings:
        by_type.setdefault(f.type, []).append(f)
    for t in sorted(by_type.keys()):
        lines.append(f"[{t}] {len(by_type[t])}")
        for f in by_type[t]:
            rel = os.path.relpath(f.file)
            lines.append(f"- {rel}:{f.line} - {f.message}")
        lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Python project checkup")
    parser.add_argument("--path", default=".", help="Root path to scan")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--ignore", nargs="*", default=[], help="Directory names to ignore")
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    ignore_dirs = DEFAULT_IGNORE_DIRS.union(set(args.ignore))

    findings: List[Finding] = []
    files_scanned = 0
    for pyfile in iter_python_files(root, ignore_dirs):
        text = safe_read_text(pyfile)
        if not text:
            continue
        files_scanned += 1
        findings.extend(scan_placeholders(pyfile, text))
        findings.extend(scan_dummy_endpoints(pyfile, text))
        findings.extend(scan_integration_red_flags(pyfile, text))
        findings.extend(scan_ast_patterns(pyfile, text))
        findings.extend(scan_print_usage(pyfile, text))

    summary = Summary(
        files_scanned=files_scanned,
        findings_count=len(findings),
        categories={},
    )
    for f in findings:
        summary.categories[f.type] = summary.categories.get(f.type, 0) + 1

    repo_meta = repo_checks(root)

    if args.output == "json":
        out = {
            "summary": asdict(summary),
            "repository": repo_meta,
            "findings": [asdict(f) for f in findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(format_text(summary, findings, repo_meta))

    return 0


if __name__ == "__main__":
    sys.exit(main())


