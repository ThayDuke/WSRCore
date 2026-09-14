"""Pure, conservative detectors for WSR Audit.

The module returns findings only. It never writes files, invokes subprocesses,
or decides that a finding is safe to auto-fix.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path

SEVERITY_WEIGHT = {"BLOCKER": 25, "HIGH": 10, "MEDIUM": 4, "LOW": 1, "INFO": 0}
CATEGORIES = ("integrity", "structure", "minimality", "dependency", "resource", "ide")
try:
    STDLIB_MODULES = set(sys.stdlib_module_names)
except AttributeError:
    STDLIB_MODULES = set(sys.builtin_module_names)
    stdlib_dir = Path(sysconfig.get_paths().get("stdlib", ""))
    if stdlib_dir.is_dir():
        STDLIB_MODULES.update(item.stem for item in stdlib_dir.glob("*.py"))
RULES = {
    "INT-001": ("integrity", "BLOCKER", "Invalid UTF-8"),
    "INT-002": ("integrity", "HIGH", "Unsafe replacement character or NUL"),
    "INT-003": ("integrity", "HIGH", "Parser failure"),
    "INT-004": ("integrity", "INFO", "Zero coverage"),
    "STR-001": ("structure", "HIGH", "Duplicate canonical rule ID"),
    "STR-002": ("structure", "MEDIUM", "Exact duplicated policy block"),
    "STR-003": ("structure", "HIGH", "Hardcoded IDE or runtime path"),
    "STR-004": ("structure", "HIGH", "Alias workflow contains independent logic"),
    "MIN-001": ("minimality", "MEDIUM", "Duplicate Python function body"),
    "MIN-002": ("minimality", "LOW", "Oversized Python symbol"),
    "MIN-003": ("minimality", "HIGH", "Unreachable statement"),
    "DEP-001": ("dependency", "MEDIUM", "Unused Python import"),
    "DEP-002": ("dependency", "MEDIUM", "Duplicate dependency declaration"),
    "DEP-003": ("dependency", "MEDIUM", "Undeclared external import"),
    "DEP-004": ("dependency", "LOW", "Stdlib replacement candidate"),
}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    category: str
    severity: str
    confidence: str
    path: str
    line: int | None
    message: str
    evidence: dict
    recommendation: str
    estimated_line_reduction: int | None = None
    estimated_dependency_reduction: int | None = None

    def as_dict(self) -> dict:
        return {
            "ruleId": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "path": self.path,
            "line": self.line,
            "message": self.message,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "estimatedLineReduction": self.estimated_line_reduction,
            "estimatedDependencyReduction": self.estimated_dependency_reduction,
        }


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def finding(rule_id: str, path: str, line: int | None, message: str,
            evidence: dict, recommendation: str, confidence: str = "high",
            severity: str | None = None, lines: int | None = None,
            dependencies: int | None = None) -> Finding:
    category, default_severity, _ = RULES[rule_id]
    return Finding(rule_id, category, severity or default_severity, confidence,
                   normalize_path(path), line, message, evidence,
                   recommendation, lines, dependencies)


def _text_extensions() -> set[str]:
    return {".py", ".pyw", ".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".ini", ".ps1", ".js", ".ts", ".html", ".css"}


def read_text(path: Path) -> tuple[str | None, Finding | None, bool]:
    data = path.read_bytes()
    ext = path.suffix.lower()
    is_binary = b"\x00" in data[:8192] and ext not in _text_extensions()
    if is_binary or ext not in _text_extensions():
        return None, None, True
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, finding("INT-001", str(path), None, "Text is not valid UTF-8",
                             {"error": str(exc)}, "Rewrite the file as UTF-8 without data loss"), False
    if "\ufffd" in text or "\x00" in text:
        return text, finding("INT-002", str(path), next((i for i, x in enumerate(text.splitlines(), 1) if "\ufffd" in x or "\x00" in x), None),
                             "Text contains U+FFFD or NUL", {"replacementChar": "\ufffd" in text, "nul": "\x00" in text},
                             "Repair encoding and remove embedded NUL bytes"), False
    return text, None, False


def parse_file(path: Path, text: str) -> list[Finding]:
    out: list[Finding] = []
    if path.suffix.lower() in {".py", ".pyw"}:
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            return [finding("INT-003", str(path), exc.lineno, "Python AST parse failed", {"error": str(exc)}, "Fix syntax before structural audit")]
        out.extend(_python_findings(path, text, tree))
    elif path.suffix.lower() == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            out.append(finding("INT-003", str(path), exc.lineno, "JSON parse failed", {"error": str(exc)}, "Fix JSON syntax before release"))
    return out


def _python_findings(path: Path, text: str, tree: ast.AST) -> list[Finding]:
    out: list[Finding] = []
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    for node in functions + classes:
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        if end - start + 1 > 120:
            out.append(finding("MIN-002", str(path), start, "Python symbol exceeds 120 lines",
                               {"symbol": getattr(node, "name", "<anonymous>"), "lines": end - start + 1},
                               "Review whether the symbol has independent responsibilities", "medium"))
    body_hashes: dict[str, tuple[ast.AST, str]] = {}
    for node in functions:
        body = ast.dump(ast.Module(body=node.body, type_ignores=[]), annotate_fields=True, include_attributes=False)
        if len(node.body) >= 5 and body in body_hashes:
            other, other_name = body_hashes[body]
            out.append(finding("MIN-001", str(path), node.lineno, "Function body duplicates another function",
                               {"symbol": node.name, "duplicateOf": other_name}, "Extract shared logic or keep one deliberate wrapper", "high"))
        else:
            body_hashes[body] = (node, node.name)
    for parent in ast.walk(tree):
        if not isinstance(parent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.For, ast.While, ast.If, ast.Try, ast.With, ast.AsyncWith, ast.ExceptHandler)):
            continue
        block = getattr(parent, "body", [])
        terminated = False
        for stmt in block:
            if terminated:
                out.append(finding("MIN-003", str(path), stmt.lineno, "Statement is unreachable after terminator",
                                   {"after": "return/raise/break/continue"}, "Remove unreachable statement or correct control flow", "high"))
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                terminated = True
    loaded = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    exported = _module_exports(tree)
    for node in getattr(tree, "body", []):
        if not isinstance(node, (ast.Import, ast.ImportFrom)) or (isinstance(node, ast.ImportFrom) and node.module == "__future__"):
            continue
        if any(alias.name == "*" for alias in node.names):
            continue
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            if local not in loaded and local not in exported and not local.startswith("_"):
                out.append(finding("DEP-001", str(path), node.lineno, "Top-level import is never loaded",
                                   {"import": alias.name, "local": local}, "Remove the import only after API/re-export review", "medium"))
    return out


def _string_constants(node: ast.AST) -> set[str]:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return set()
    return {
        item.value for item in node.elts
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    }


def _module_exports(tree: ast.AST) -> set[str]:
    exported: set[str] = set()
    for node in getattr(tree, "body", []):
        value = None
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
            value = node.value
        if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            exported.update(_string_constants(value) if value is not None else set())
    return exported


RULE_LINE = re.compile(r"^\s*(?:[-*]\s*)?([A-Z][A-Z0-9_]*-\d{2,})\s*[:—-]")
PATH_LITERAL = re.compile(r"(?:~/(?:\.codex|\.agents|\.gemini|\.config)|%USERPROFILE%|%APPDATA%|[A-Za-z]:[/\\](?![/\\]).+|file:///|\.agents/scripts|\.gemini/config|\.codex/)")


def markdown_findings(path: Path, text: str) -> list[Finding]:
    out: list[Finding] = []
    rule_defs: dict[str, int] = {}
    blocks: dict[str, tuple[str, int]] = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        match = RULE_LINE.match(line)
        if match:
            rid = match.group(1)
            if rid in rule_defs:
                out.append(finding("STR-001", str(path), line_no, "Rule ID has multiple canonical definitions",
                                   {"ruleId": rid, "firstLine": rule_defs[rid]}, "Keep one canonical definition and convert others to references"))
            else:
                rule_defs[rid] = line_no
        normalized = " ".join(line.strip().lower().split())
        if len(normalized) >= 80 and len(normalized.split()) >= 12:
            blocks.setdefault(normalized, (str(path), line_no))
    canonical_scope = any(part in {"global_workflows", "skills", "global_rules"} for part in path.parts) or path.name in {"GEMINI.md", "AGENTS.md"}
    if canonical_scope and PATH_LITERAL.search(text):
        out.append(finding("STR-003", str(path), None, "Canonical text contains an IDE or runtime-specific path",
                           {"matched": PATH_LITERAL.search(text).group(0)}, "Use adapter metadata or a logical path"))
    if path.name.lower() in {"ho.md", "handoff.md"} and "alias" in text.lower():
        substantive = [x for x in text.splitlines() if x.strip() and not x.strip().startswith(("#", "---", "description:"))]
        if len(substantive) > 4:
            out.append(finding("STR-004", str(path), None, "Alias workflow contains independent instructions",
                               {"substantiveLines": len(substantive)}, "Make the alias redirect to the canonical workflow", "high"))
    return out


def _duplicate_policy_scope(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if path.suffix.lower() != ".md" or parts & {"docs", "evidence", "references"}:
        return False
    if name in {"readme.md", "changelog.md"}:
        return False
    return (
        name in {"agents.md", "gemini.md", "skill.md"}
        or bool(parts & {"global_rules", "global_workflows", "skills", "global_skills"})
    )


def duplicate_blocks(files: list[tuple[Path, str]]) -> list[Finding]:
    seen: dict[str, tuple[Path, int]] = {}
    out: list[Finding] = []
    for path, text in files:
        if not _duplicate_policy_scope(path):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            normalized = " ".join(line.strip().lower().split())
            if len(normalized) < 80 or len(normalized.split()) < 12:
                continue
            previous = seen.get(normalized)
            if previous and previous[0] != path:
                out.append(finding("STR-002", str(path), line_no, "Exact policy block is duplicated across files",
                                   {"duplicateOf": normalize_path(str(previous[0])), "firstLine": previous[1]}, "Keep one canonical block and reference it", "high"))
            else:
                seen[normalized] = (path, line_no)
    return out


def _dependency_name(spec: str) -> str | None:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", spec)
    if not match:
        return None
    return match.group(1).lower().replace("_", "-")


def _requirement_file(path: Path) -> bool:
    name = path.name.lower()
    parents = {part.lower() for part in path.parts}
    return (
        path.suffix.lower() == ".txt"
        and (name.startswith(("requirements", "constraints")) or bool(parents & {"requirements", "constraints"}))
    )


def _minimum_python_at_least(spec: str | None, target: tuple[int, int]) -> bool:
    if not spec or "||" in spec:
        return False
    lower_bounds: list[tuple[int, int]] = []
    for match in re.finditer(r"(?<![<>=!~])(>=|>)\s*(\d+)\.(\d+)", spec):
        version = (int(match.group(2)), int(match.group(3)))
        if match.group(1) == ">":
            version = (version[0], version[1] + 1)
        lower_bounds.append(version)
    return bool(lower_bounds) and max(lower_bounds) >= target


def _pyproject_declarations(path: Path) -> tuple[list[tuple[str, int]], str | None]:
    declarations: list[tuple[str, int]] = []
    requires_python = None
    section = ""
    array_section = None
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeDecodeError):
        return declarations, requires_python
    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        header = re.fullmatch(r"\[([^]]+)\]", line)
        if header:
            section = header.group(1).strip().lower()
            array_section = None
            continue
        if not line or line.startswith("#"):
            continue
        if section == "project":
            match = re.match(r"requires-python\s*=\s*([\"'])(.*?)\1\s*(?:#.*)?$", line, re.I)
            if match:
                requires_python = match.group(2)
                continue
            if re.match(r"dependencies\s*=", line, re.I):
                array_section = "dependencies" if "[" in line and "]" not in line else None
                for value in re.findall(r"[\"']([^\"']+)[\"']", line.split("=", 1)[1]):
                    name = _dependency_name(value)
                    if name:
                        declarations.append((name, line_no))
                continue
        if section in {"project.optional-dependencies", "dependency-groups"} and "=" in line and "[" in line:
            array_section = section if "]" not in line else None
            for value in re.findall(r"[\"']([^\"']+)[\"']", line.split("=", 1)[1]):
                name = _dependency_name(value)
                if name:
                    declarations.append((name, line_no))
            continue
        if section == "tool.poetry.dependencies" and "=" in line:
            key = line.split("=", 1)[0].strip().strip("\"'")
            name = _dependency_name(key)
            if name and name != "python":
                declarations.append((name, line_no))
            continue
        if array_section:
            for value in re.findall(r"[\"']([^\"']+)[\"']", line):
                name = _dependency_name(value)
                if name:
                    declarations.append((name, line_no))
            if "]" in line:
                array_section = None
    return declarations, requires_python


def dependency_findings(root: Path, files: list[tuple[Path, str]], excluded_dirs: set[str] | None = None) -> list[Finding]:
    excluded = set(excluded_dirs or ())
    declarations: dict[str, tuple[Path, int]] = {}
    pyproject_requires = None
    declaration_rows: list[tuple[str, Path, int]] = []
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in excluded]
        for filename in names:
            path = Path(current) / filename
            if path.name.lower() == "pyproject.toml":
                parsed, requires_python = _pyproject_declarations(path)
                pyproject_requires = requires_python or pyproject_requires
                declaration_rows.extend((name, path, line_no) for name, line_no in parsed)
            elif _requirement_file(path):
                try:
                    text = path.read_text(encoding="utf-8", errors="strict")
                except (OSError, UnicodeDecodeError):
                    continue
                for line_no, raw in enumerate(text.splitlines(), 1):
                    line = raw.strip()
                    if not line or line.startswith(("#", ";", "-e ", "--", "-r ")):
                        continue
                    name = _dependency_name(line)
                    if name:
                        declaration_rows.append((name, path, line_no))
    for name, path, line_no in declaration_rows:
        if name in declarations:
            prior, prior_line = declarations[name]
            yield finding("DEP-002", str(path), line_no, "Dependency declaration is duplicated",
                          {"dependency": name, "duplicateOf": normalize_path(str(prior)), "firstLine": prior_line}, "Keep one declaration source", "high")
        else:
            declarations[name] = (path, line_no)
    local_modules = {path.stem for path, text in files if path.suffix.lower() == ".py"}
    local_modules.update(path.name for path in root.iterdir() if path.is_dir() and (path / "__init__.py").is_file())
    stdlib_replacement_allowed = _minimum_python_at_least(pyproject_requires, (3, 11))
    for path, text in files:
        if path.suffix.lower() != ".py":
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            match = re.match(r"\s*import\s+([A-Za-z_][\w.]*)|\s*from\s+([A-Za-z_][\w.]*)\s+import", line)
            if not match:
                continue
            module = (match.group(1) or match.group(2)).split(".")[0]
            if module in STDLIB_MODULES or module in {"tests", "scripts"} or module in local_modules:
                continue
            normalized = module.lower().replace("_", "-")
            if normalized not in declarations:
                yield finding("DEP-003", str(path), line_no, "External import has no declaration found",
                              {"module": module}, "Declare the dependency or confirm it is a local module", "medium")
            if normalized == "tomli" and stdlib_replacement_allowed:
                yield finding("DEP-004", str(path), line_no, "tomli may be replaced by stdlib tomllib",
                              {"module": module, "requiresPython": ">=3.11"}, "Use tomllib only when supported Python is guaranteed", "medium", severity="LOW", dependencies=1)


def file_findings(root: Path, path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(parse_file(path, text))
    if path.suffix.lower() in {".md", ".txt", ".yaml", ".yml"}:
        findings.extend(markdown_findings(path, text))
    return findings
