#!/usr/bin/env python3
"""
Skill Vetter Plus — Automated Security Scanner
Cross-platform (macOS / Windows / Linux). Requires Python 3.7+.

Usage:
    python3 scan_skill.py /path/to/skill-directory
    python3 scan_skill.py /path/to/skill.zip
    python3 scan_skill.py /path/to/SKILL.md          # single file

Options:
    --sensitive-paths FILE   Custom sensitive paths file (one pattern per line)
    --json                   Output as JSON instead of human-readable report
    --quiet                  Only print PASS/WARN/FAIL summary line
"""

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, NamedTuple

# ──────────────────────────────────────────────────────────────
# Data types
# ──────────────────────────────────────────────────────────────

class Finding(NamedTuple):
    severity: str        # "critical" | "warning" | "info"
    category: str
    file: str
    line: int            # 0 = file-level
    description: str
    evidence: str        # the matching text snippet


# ──────────────────────────────────────────────────────────────
# Default sensitive path patterns
# ──────────────────────────────────────────────────────────────

# Sensitive patterns are split into two tiers:
#   - PATH patterns: match filesystem paths (high-signal, always critical)
#   - KEYWORD patterns: match variable/param names (lower-signal, warning only)
#     Keywords use word-boundary + context to reduce false positives on
#     normal variable names like page_token, obj_token, block_key, etc.

SENSITIVE_PATH_PATTERNS = [
    # Credential & config directories
    r"~/\.ssh",
    r"~/\.aws",
    r"~/\.gnupg",
    r"~/\.netrc\b",
    r"~/\.npmrc\b",
    r"~/\.pypirc\b",
    r"~/\.docker",
    r"~/\.kube",
    r"~/\.config/",
    # Agent identity & memory
    r"~/\.claude/memory",
    r"~/\.claude/CLAUDE\.md",
    r"\bMEMORY\.md\b",
    r"\bUSER\.md\b",
    r"\bSOUL\.md\b",
    r"\bIDENTITY\.md\b",
    # Other skills (reading other skills' code)
    r"~/\.claude/skills/(?!skill-vetter)",
    # Env files
    r"\.env\b(?!iron)",  # .env but not .environ
]

SENSITIVE_KEYWORD_PATTERNS = [
    # These match credential-like references in code but use stricter context
    # to avoid false positives on normal variable names
    r"(?:credentials|credential)\.(?:json|yaml|yml|xml|txt|cfg)",
    r"(?:read|open|load|parse|cat)\s.*(?:password|passwd|secret|credential)",
    r"(?:api[_-]?key|secret[_-]?key|auth[_-]?token|access[_-]?token)\s*[=:]",
    r"(?:cookie|cookies)\.(?:get|set|delete|txt|json)",
]

# ──────────────────────────────────────────────────────────────
# Invisible / suspicious Unicode ranges
# ──────────────────────────────────────────────────────────────

INVISIBLE_CHARS = {
    "\u200b": "ZERO WIDTH SPACE",
    "\u200c": "ZERO WIDTH NON-JOINER",
    "\u200d": "ZERO WIDTH JOINER",
    "\u200e": "LEFT-TO-RIGHT MARK",
    "\u200f": "RIGHT-TO-LEFT MARK",
    "\u202a": "LEFT-TO-RIGHT EMBEDDING",
    "\u202b": "RIGHT-TO-LEFT EMBEDDING",
    "\u202c": "POP DIRECTIONAL FORMATTING",
    "\u202d": "LEFT-TO-RIGHT OVERRIDE",
    "\u202e": "RIGHT-TO-LEFT OVERRIDE",
    "\u2060": "WORD JOINER",
    "\u2061": "FUNCTION APPLICATION",
    "\u2062": "INVISIBLE TIMES",
    "\u2063": "INVISIBLE SEPARATOR",
    "\u2064": "INVISIBLE PLUS",
    "\ufeff": "BYTE ORDER MARK (mid-file)",
    "\ufff9": "INTERLINEAR ANNOTATION ANCHOR",
    "\ufffa": "INTERLINEAR ANNOTATION SEPARATOR",
    "\ufffb": "INTERLINEAR ANNOTATION TERMINATOR",
    "\U000e0001": "LANGUAGE TAG",
}

# Homoglyph pairs (Cyrillic/Greek lookalikes for Latin)
HOMOGLYPHS = {
    "\u0410": "А (Cyrillic A)",
    "\u0412": "В (Cyrillic V, looks like B)",
    "\u0421": "С (Cyrillic S, looks like C)",
    "\u0415": "Е (Cyrillic Ye, looks like E)",
    "\u041d": "Н (Cyrillic En, looks like H)",
    "\u041a": "К (Cyrillic Ka, looks like K)",
    "\u041c": "М (Cyrillic Em, looks like M)",
    "\u041e": "О (Cyrillic O)",
    "\u0420": "Р (Cyrillic Er, looks like P)",
    "\u0422": "Т (Cyrillic Te, looks like T)",
    "\u0425": "Х (Cyrillic Kha, looks like X)",
    "\u0430": "а (Cyrillic a)",
    "\u0435": "е (Cyrillic ye, looks like e)",
    "\u043e": "о (Cyrillic o)",
    "\u0440": "р (Cyrillic er, looks like p)",
    "\u0441": "с (Cyrillic es, looks like c)",
    "\u0443": "у (Cyrillic u, looks like y)",
    "\u0445": "х (Cyrillic kha, looks like x)",
}

# ──────────────────────────────────────────────────────────────
# Regex patterns for each check category
# ──────────────────────────────────────────────────────────────

PATTERNS: Dict[str, List[tuple]] = {
    "obfuscation": [
        (r"base64[._]?(?:decode|b64decode|atob)\s*\(", "critical",
         "Base64 decode call"),
        (r"\\x[0-9a-fA-F]{2}(?:\\x[0-9a-fA-F]{2}){3,}", "warning",
         "Hex-encoded string (4+ bytes)"),
        (r"\beval\s*\(", "critical",
         "eval() call — arbitrary code execution"),
        (r"\bexec\s*\(", "critical",
         "exec() call — arbitrary code execution"),
        (r"\bcompile\s*\(.+(?:exec|eval)", "critical",
         "compile() with exec/eval mode"),
        (r"(?:rot13|codecs\.decode.*rot)", "warning",
         "ROT13 encoding detected"),
        (r"fromCharCode|chr\s*\(\s*\d+\s*\)", "warning",
         "Character code construction"),
    ],

    "network_exfil": [
        (r"curl\s+.*-[dX]\s*POST|curl\s+.*--data", "critical",
         "curl POST — potential data exfiltration"),
        (r"wget\s+.*--post", "critical",
         "wget POST — potential data exfiltration"),
        (r"requests\.post\s*\(", "critical",
         "Python requests.post — potential data exfiltration"),
        (r"fetch\s*\(.+method\s*:\s*['\"]POST", "critical",
         "fetch POST — potential data exfiltration"),
        (r"urllib\.request\.urlopen|urllib\.request\.Request", "warning",
         "urllib network call"),
        (r"http\.client\.HTTP", "warning",
         "http.client network call"),
        (r"socket\.(?:connect|send)", "critical",
         "Raw socket operation"),
        (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b(?!.*(?:127\.0\.0\.1|0\.0\.0\.0|localhost))",
         "warning", "IP address (not localhost) — prefer domain names"),
        (r"curl\s|wget\s|requests\.get|httpx\.", "warning",
         "Network call (GET) — verify destination"),
    ],

    "credential_harvest": [
        (r"(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[=:]",
         "critical", "Credential assignment/access pattern"),
        (r"open\s*\(.*(?:password|credential|secret|token|key).*\)", "critical",
         "Reading file with credential-like name"),
        (r"os\.environ\s*\[.*(?:KEY|SECRET|TOKEN|PASSWORD|CRED)", "warning",
         "Reading sensitive environment variable"),
        (r"keychain|keyring|credential.?manager", "warning",
         "System credential store access"),
    ],

    "permission_escalation": [
        (r"\bsudo\b", "critical",
         "sudo — root privilege escalation"),
        (r"\bchmod\s+[0-7]*[4-7][0-7]{2}\b|chmod\s+\+[sx]", "warning",
         "chmod — permission change"),
        (r"\bchown\b", "warning",
         "chown — ownership change"),
        (r"setuid|setgid|capabilities", "warning",
         "Privilege escalation pattern"),
    ],

    "package_install": [
        (r"pip\s+install(?!\s+--)", "warning",
         "pip install — verify packages are expected"),
        (r"npm\s+install|yarn\s+add|pnpm\s+add", "warning",
         "npm/yarn package install — verify packages"),
        (r"brew\s+install|apt\s+install|yum\s+install", "warning",
         "System package install"),
        (r"gem\s+install|cargo\s+install", "warning",
         "Package install — verify expected"),
    ],

    "prompt_injection": [
        (r"ignore\s+(?:previous|prior|above|all)\s+instructions", "critical",
         "Prompt injection — instruction override"),
        (r"you\s+are\s+now\b", "critical",
         "Prompt injection — identity override"),
        (r"do\s+not\s+(?:mention|tell|inform|reveal|show)\s+(?:the\s+)?user", "critical",
         "Secrecy clause — hiding behavior from user"),
        (r"pretend\s+(?:you|to\s+be)", "warning",
         "Role override attempt"),
        (r"system\s*:\s*you\s+are", "critical",
         "System prompt injection"),
        (r"<\s*system\s*>|<\s*/\s*system\s*>", "critical",
         "System tag injection"),
    ],

    "hidden_content": [
        (r"<!--[\s\S]*?-->", "warning",
         "HTML comment — check for hidden instructions"),
    ],

    "conditional_trigger": [
        (r"if\s+.*(?:os\.name|sys\.platform|platform\.system)", "warning",
         "Platform-conditional code — verify purpose"),
        (r"if\s+.*(?:datetime|time\.time|date\.today)", "warning",
         "Time-conditional code — potential delayed trigger"),
        (r"if\s+.*os\.path\.exists.*(?:\.ssh|\.aws|\.config|\.claude)", "critical",
         "Conditional check for sensitive paths"),
        (r"if\s+.*os\.environ\.get\s*\(", "warning",
         "Environment-conditional code — verify purpose"),
    ],

    "system_modification": [
        (r"shutil\.rmtree|os\.remove|os\.unlink|pathlib.*\.unlink", "warning",
         "File deletion operation"),
        (r"(?:open|write|Path).*(?:\/etc\/|\\Windows\\|\\System32)", "critical",
         "System file modification"),
        (r"os\.system\s*\(|subprocess\.\w+\s*\(", "warning",
         "Shell command execution — verify command"),
        (r"crontab|schtasks|launchctl|systemctl", "critical",
         "Scheduled task modification"),
    ],
}


# ──────────────────────────────────────────────────────────────
# Scanner implementation
# ──────────────────────────────────────────────────────────────

def load_sensitive_patterns(custom_file: str = None):
    """Load sensitive patterns from defaults + optional custom file.
    Returns (path_patterns, keyword_patterns) tuple."""
    path_pats = list(SENSITIVE_PATH_PATTERNS)
    kw_pats = list(SENSITIVE_KEYWORD_PATTERNS)
    if custom_file and os.path.isfile(custom_file):
        with open(custom_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    path_pats.append(re.escape(line).replace(r"\*", ".*"))
    return path_pats, kw_pats


def get_text_files(directory: Path) -> List[Path]:
    """Recursively find text files, skipping binaries and common non-text."""
    skip_extensions = {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
        ".mp3", ".mp4", ".wav", ".avi", ".mov",
        ".zip", ".gz", ".tar", ".bz2", ".7z", ".rar",
        ".exe", ".dll", ".so", ".dylib",
        ".pyc", ".pyo", ".class", ".o",
        ".woff", ".woff2", ".ttf", ".eot",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    }
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}
    files = []
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in filenames:
            fp = Path(root) / fname
            if fp.suffix.lower() not in skip_extensions:
                files.append(fp)
    return files


def scan_file(filepath: Path, sensitive_path_patterns: List[str],
              sensitive_keyword_patterns: List[str]) -> List[Finding]:
    """Scan a single file for all security issues."""
    findings: List[Finding] = []
    rel = str(filepath)

    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        findings.append(Finding("info", "read_error", rel, 0,
                                f"Could not read file: {e}", ""))
        return findings

    lines = content.split("\n")

    # ── Check invisible characters ──
    for i, line in enumerate(lines, 1):
        for char, name in INVISIBLE_CHARS.items():
            if char in line:
                # Skip BOM at start of file
                if char == "\ufeff" and i == 1 and line.startswith("\ufeff"):
                    continue
                findings.append(Finding(
                    "critical", "invisible_char", rel, i,
                    f"Invisible character: {name} (U+{ord(char):04X})",
                    repr(line[:80])
                ))

    # ── Check homoglyphs (only in non-.py files or outside string literals) ──
    # For .py files containing homoglyph *definitions*, skip.
    is_homoglyph_def_file = filepath.name == "scan_skill.py"
    if not is_homoglyph_def_file:
        for i, line in enumerate(lines, 1):
            for char, name in HOMOGLYPHS.items():
                if char in line:
                    findings.append(Finding(
                        "warning", "homoglyph", rel, i,
                        f"Homoglyph character: {name}",
                        repr(line[:80])
                    ))

    # ── Regex pattern checks ──
    for category, rules in PATTERNS.items():
        for pattern, severity, desc in rules:
            try:
                for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                    line_num = content[:match.start()].count("\n") + 1
                    match_line = lines[line_num - 1] if line_num <= len(lines) else ""
                    evidence = match_line.strip()[:120]
                    findings.append(Finding(
                        severity, category, rel, line_num,
                        desc, evidence
                    ))
            except re.error:
                pass

    # ── Sensitive path access (critical) ──
    for pattern in sensitive_path_patterns:
        try:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count("\n") + 1
                match_line = lines[line_num - 1] if line_num <= len(lines) else ""
                findings.append(Finding(
                    "critical", "sensitive_path", rel, line_num,
                    f"References sensitive path: {match.group()[:60]}",
                    match_line.strip()[:120]
                ))
        except re.error:
            pass

    # ── Sensitive keyword access (warning — lower confidence) ──
    for pattern in sensitive_keyword_patterns:
        try:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count("\n") + 1
                match_line = lines[line_num - 1] if line_num <= len(lines) else ""
                findings.append(Finding(
                    "warning", "sensitive_keyword", rel, line_num,
                    f"Sensitive keyword pattern: {match.group()[:60]}",
                    match_line.strip()[:120]
                ))
        except re.error:
            pass

    return findings


def scan_directory(directory: Path, sensitive_path_patterns: List[str],
                   sensitive_keyword_patterns: List[str]) -> List[Finding]:
    """Scan all text files in a directory."""
    all_findings: List[Finding] = []
    files = get_text_files(directory)

    if not files:
        all_findings.append(Finding(
            "info", "empty", str(directory), 0,
            "No text files found in directory", ""
        ))
        return all_findings

    for fp in files:
        file_findings = scan_file(fp, sensitive_path_patterns, sensitive_keyword_patterns)
        all_findings.extend(file_findings)

    return all_findings


def deduplicate_findings(findings: List[Finding]) -> List[Finding]:
    """Remove duplicate findings (same file + line + category)."""
    seen = set()
    unique = []
    for f in findings:
        key = (f.file, f.line, f.category, f.description)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def filter_self_references(findings: List[Finding], scan_target: Path) -> List[Finding]:
    """
    If we're scanning a security-oriented skill, it may *mention* dangerous
    patterns as part of its checklist (like Skill Vetter itself does).
    We keep findings but mark context to help the reviewer.
    """
    return findings  # Keep all — the report shows context for human judgment


# ──────────────────────────────────────────────────────────────
# Output formatting
# ──────────────────────────────────────────────────────────────

SEVERITY_ICON = {"critical": "🚨", "warning": "⚠️ ", "info": "ℹ️ "}
SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def format_report(findings: List[Finding], target: str) -> str:
    """Format findings as a human-readable report."""
    findings = sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 9))

    criticals = [f for f in findings if f.severity == "critical"]
    warnings = [f for f in findings if f.severity == "warning"]
    infos = [f for f in findings if f.severity == "info"]

    if criticals:
        verdict = "FAIL"
        verdict_icon = "❌"
    elif warnings:
        verdict = "WARNINGS"
        verdict_icon = "⚠️"
    else:
        verdict = "PASS"
        verdict_icon = "✅"

    lines = []
    lines.append("╔══════════════════════════════════════════════════════╗")
    lines.append("║        SKILL VETTER PLUS — AUTOMATED SCAN          ║")
    lines.append("╚══════════════════════════════════════════════════════╝")
    lines.append("")
    lines.append(f"  Target:    {target}")
    lines.append(f"  Result:    {verdict_icon} {verdict}")
    lines.append(f"  Criticals: {len(criticals)}")
    lines.append(f"  Warnings:  {len(warnings)}")
    lines.append(f"  Info:      {len(infos)}")
    lines.append("")

    if not findings:
        lines.append("  No issues found. Proceed to manual review.")
        lines.append("")
        return "\n".join(lines)

    lines.append("──────────────────────────────────────────────────────")

    current_file = None
    for f in findings:
        if f.file != current_file:
            current_file = f.file
            lines.append("")
            lines.append(f"  📄 {f.file}")
            lines.append("  " + "─" * 50)

        icon = SEVERITY_ICON.get(f.severity, "  ")
        loc = f"L{f.line}" if f.line > 0 else "file"
        lines.append(f"  {icon} [{f.severity.upper()}] {loc}: {f.description}")
        if f.evidence:
            ev = f.evidence[:100]
            lines.append(f"       │ {ev}")

    lines.append("")
    lines.append("══════════════════════════════════════════════════════")
    lines.append(f"  VERDICT: {verdict_icon} {verdict}")
    if criticals:
        lines.append("  ➜ CRITICAL issues found. DO NOT INSTALL without")
        lines.append("    thorough manual review and human approval.")
    elif warnings:
        lines.append("  ➜ Warnings found. Review each item manually.")
        lines.append("    May be benign — context matters.")
    else:
        lines.append("  ➜ Automated checks passed. Proceed to manual review.")
    lines.append("══════════════════════════════════════════════════════")
    lines.append("")

    return "\n".join(lines)


def format_json(findings: List[Finding], target: str) -> str:
    """Format findings as JSON."""
    criticals = [f for f in findings if f.severity == "critical"]
    warnings = [f for f in findings if f.severity == "warning"]

    if criticals:
        verdict = "FAIL"
    elif warnings:
        verdict = "WARNINGS"
    else:
        verdict = "PASS"

    data = {
        "target": target,
        "verdict": verdict,
        "summary": {
            "critical": len(criticals),
            "warning": len(warnings),
            "info": len([f for f in findings if f.severity == "info"]),
        },
        "findings": [
            {
                "severity": f.severity,
                "category": f.category,
                "file": f.file,
                "line": f.line,
                "description": f.description,
                "evidence": f.evidence,
            }
            for f in findings
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Skill Vetter Plus — Automated Security Scanner",
        epilog="Run this before installing any AI agent skill.",
    )
    parser.add_argument("target",
                        help="Path to skill directory, zip file, or single file")
    parser.add_argument("--sensitive-paths",
                        help="Custom sensitive paths file (one pattern per line)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output as JSON")
    parser.add_argument("--quiet", action="store_true",
                        help="Only print PASS/WARN/FAIL")
    args = parser.parse_args()

    target = Path(args.target).resolve()

    # Find custom sensitive paths file (check alongside script, then skill dir)
    custom_sensitive = args.sensitive_paths
    if not custom_sensitive:
        # Check default location
        script_dir = Path(__file__).resolve().parent.parent
        default_sp = script_dir / "sensitive_paths.txt"
        if default_sp.is_file():
            custom_sensitive = str(default_sp)

    path_pats, kw_pats = load_sensitive_patterns(custom_sensitive)

    # Handle zip files
    temp_dir = None
    scan_path = target
    if target.is_file() and target.suffix.lower() == ".zip":
        temp_dir = tempfile.mkdtemp(prefix="skill_vetter_")
        scan_path = Path(temp_dir)
        with zipfile.ZipFile(target, "r") as zf:
            zf.extractall(scan_path)
        print(f"Extracted zip to temp directory for scanning...", file=sys.stderr)

    # Scan
    try:
        if scan_path.is_file():
            findings = scan_file(scan_path, path_pats, kw_pats)
        elif scan_path.is_dir():
            findings = scan_directory(scan_path, path_pats, kw_pats)
        else:
            print(f"Error: {target} is not a file or directory", file=sys.stderr)
            sys.exit(1)
    finally:
        # Clean up temp dir
        if temp_dir:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    findings = deduplicate_findings(findings)

    # Output
    criticals = [f for f in findings if f.severity == "critical"]
    warnings = [f for f in findings if f.severity == "warning"]

    if args.quiet:
        if criticals:
            print("FAIL")
            sys.exit(2)
        elif warnings:
            print("WARNINGS")
            sys.exit(1)
        else:
            print("PASS")
            sys.exit(0)

    if args.json_output:
        print(format_json(findings, str(target)))
    else:
        print(format_report(findings, str(target)))

    # Exit code: 2 = critical, 1 = warnings, 0 = clean
    if criticals:
        sys.exit(2)
    elif warnings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
