# Skill Vetter Plus 🔒

Security-first skill vetting for AI agents — **manual checklist + automated scanner**.

> Based on [Skill Vetter by @spclaudehome](https://clawhub.ai/spclaudehome/skill-vetter) (MIT-0),
> extended with automated scanning, cross-platform support, and deeper threat coverage.

## What It Does

Before installing any skill from ClawHub, GitHub, or other sources, run this tool to:

- Detect **invisible/zero-width characters** hidden in skill files
- Detect **homoglyph attacks** (Cyrillic letters disguised as Latin)
- Detect **prompt injection** patterns
- Detect **obfuscated code** (base64, eval, exec)
- Detect **data exfiltration** (curl POST, requests.post to external servers)
- Detect **credential harvesting** (reading API keys, tokens, passwords)
- Detect **sensitive path access** (~/.ssh, ~/.aws, ~/.config, ~/.claude/memory, etc.)
- Detect **permission escalation** (sudo, chmod, system file writes)
- Detect **conditional triggers** (time-based, platform-based activation)
- Apply the full **6-step manual review checklist** (source check → code review → prompt injection → permission scope → risk classification → version diff)

---

## Requirements

| Requirement | Detail |
|-------------|--------|
| Python | 3.7 or newer |
| OS | macOS / Windows / Linux |
| Dependencies | None (standard library only) |

---

## Installation

### Claude Code (Recommended — Global Skill)

Global skills are available in **every project** and **every conversation**.
Install once, use everywhere.

---

#### macOS / Linux

```bash
# 1. Find your Claude Code global skills directory
#    Default: ~/.claude/skills/
mkdir -p ~/.claude/skills/skill-vetter-plus/scripts

# 2. Download the skill files
curl -fsSL "https://raw.githubusercontent.com/qiye2014/Seven-skills/main/skill-vetter-plus/SKILL.md" \
  -o ~/.claude/skills/skill-vetter-plus/SKILL.md

curl -fsSL "https://raw.githubusercontent.com/qiye2014/Seven-skills/main/skill-vetter-plus/scripts/scan_skill.py" \
  -o ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py

curl -fsSL "https://raw.githubusercontent.com/qiye2014/Seven-skills/main/skill-vetter-plus/sensitive_paths.txt" \
  -o ~/.claude/skills/skill-vetter-plus/sensitive_paths.txt

# 3. Verify installation
python3 ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py --help
```

Or clone the entire repo and copy:

```bash
git clone https://github.com/qiye2014/Seven-skills.git /tmp/Seven-skills
cp -r /tmp/Seven-skills/skill-vetter-plus ~/.claude/skills/
```

---

#### Windows (PowerShell)

```powershell
# 1. Create the skill directory
$skillDir = "$env:USERPROFILE\.claude\skills\skill-vetter-plus"
New-Item -ItemType Directory -Force -Path "$skillDir\scripts" | Out-Null

# 2. Download the skill files
$base = "https://raw.githubusercontent.com/qiye2014/Seven-skills/main/skill-vetter-plus"
Invoke-WebRequest "$base/SKILL.md"              -OutFile "$skillDir\SKILL.md"
Invoke-WebRequest "$base/scripts/scan_skill.py" -OutFile "$skillDir\scripts\scan_skill.py"
Invoke-WebRequest "$base/sensitive_paths.txt"   -OutFile "$skillDir\sensitive_paths.txt"

# 3. Verify installation
python "$skillDir\scripts\scan_skill.py" --help
```

Or using Git:

```powershell
git clone https://github.com/qiye2014/Seven-skills.git $env:TEMP\Seven-skills
Copy-Item -Recurse "$env:TEMP\Seven-skills\skill-vetter-plus" "$env:USERPROFILE\.claude\skills\"
```

---

### OpenClaw / ClawHub

OpenClaw skills are installed per-project or globally depending on your setup.

1. Go to your OpenClaw skills directory (check your OpenClaw settings for the path)
2. Create folder `skill-vetter-plus/scripts/`
3. Copy `SKILL.md`, `scripts/scan_skill.py`, and `sensitive_paths.txt` into it

Or from your agent session:

```
/skill install https://github.com/qiye2014/Seven-skills/tree/main/skill-vetter-plus
```

---

### Verify the Installation

After installing, confirm the skill loads correctly:

**macOS / Linux:**
```bash
python3 ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py ~/.claude/skills/skill-vetter-plus/ --quiet
# Expected: WARNINGS (the skill flags its own checklist content, which is normal)
```

**Windows:**
```powershell
python "$env:USERPROFILE\.claude\skills\skill-vetter-plus\scripts\scan_skill.py" `
  "$env:USERPROFILE\.claude\skills\skill-vetter-plus\" --quiet
```

---

## Usage

### In Claude Code / OpenClaw (Conversational)

Just mention the skill in your conversation when you want to vet a new skill:

```
I want to install [skill-name] from ClawHub. Please vet it first using skill-vetter-plus.
```

The agent will:
1. Run the automated scanner (`scan_skill.py`) on the downloaded skill files
2. Complete the 6-step manual checklist
3. Produce a full vetting report with a SAFE / CAUTION / DO NOT INSTALL verdict

### Command Line (Direct Scanner)

You can also run the scanner directly without going through the agent:

```bash
# Scan a local skill directory
python3 ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py /path/to/skill/

# Scan a downloaded .zip file (from ClawHub)
python3 ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py downloaded-skill.zip

# Scan a single file
python3 ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py SKILL.md

# Machine-readable JSON output (for CI/automation)
python3 ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py /path/to/skill/ --json

# One-line PASS/WARNINGS/FAIL (for scripting)
python3 ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py /path/to/skill/ --quiet

# Use a custom sensitive paths config
python3 ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py /path/to/skill/ \
  --sensitive-paths ~/my_sensitive_paths.txt
```

**Exit codes:**
- `0` — PASS (no issues)
- `1` — WARNINGS (review recommended)
- `2` — FAIL (critical issues found, do not install without review)

---

## Custom Sensitive Paths

Edit `sensitive_paths.txt` to add paths specific to your environment:

```
# Add your own sensitive paths (one per line, supports regex)
~/my-company/secrets/
~/.vault-token
*.pem
```

---

## What the Report Looks Like

```
╔══════════════════════════════════════════════════════╗
║        SKILL VETTER PLUS — AUTOMATED SCAN          ║
╚══════════════════════════════════════════════════════╝

  Target:    /path/to/some-skill
  Result:    ❌ FAIL
  Criticals: 2
  Warnings:  3
  Info:      0

──────────────────────────────────────────────────────
  📄 some-skill/SKILL.md
  ─────────────────────────────────────────────────
  🚨 [CRITICAL] L14: Credential assignment/access pattern
       │ api_key = "sk-xxxxx..."
  🚨 [CRITICAL] L30: Python requests.post — potential data exfiltration
       │ response = requests.post(url, headers=headers, json=data)

══════════════════════════════════════════════════════
  VERDICT: ❌ FAIL
  ➜ CRITICAL issues found. DO NOT INSTALL without
    thorough manual review and human approval.
══════════════════════════════════════════════════════
```

---

## File Structure

```
skill-vetter-plus/
├── SKILL.md               # Main skill document (checklist + workflow)
├── README.md              # This file
├── sensitive_paths.txt    # Custom sensitive path patterns (editable)
└── scripts/
    └── scan_skill.py      # Automated scanner (Python 3.7+, no dependencies)
```

---

## License

MIT-0 — Free to use, modify, and redistribute. No attribution required.

Original Skill Vetter by @spclaudehome (MIT-0) · Extended by qiye2014
