# Seven Skills

A collection of Claude Code / OpenClaw skills for productivity and security.

## Skills

| Skill | Description |
|-------|-------------|
| [skill-vetter-plus](./skill-vetter-plus/) | 🔒 Security-first skill vetting with automated scanner. Run before installing any new skill. |
| [get-hot-topics](./get-hot-topics/) | 选题助手，帮助内容创作者快速找到值得写的热点话题 |
| [write-article](./write-article/) | 资深公众号深度内容创作者，生产可直接发布的深度文章 |

---

## Quick Install — skill-vetter-plus

**macOS / Linux:**
```bash
mkdir -p ~/.claude/skills/skill-vetter-plus/scripts
base="https://raw.githubusercontent.com/qiye2014/Seven-skills/main/skill-vetter-plus"
curl -fsSL "$base/SKILL.md"              -o ~/.claude/skills/skill-vetter-plus/SKILL.md
curl -fsSL "$base/scripts/scan_skill.py" -o ~/.claude/skills/skill-vetter-plus/scripts/scan_skill.py
curl -fsSL "$base/sensitive_paths.txt"   -o ~/.claude/skills/skill-vetter-plus/sensitive_paths.txt
```

**Windows (PowerShell):**
```powershell
$d = "$env:USERPROFILE\.claude\skills\skill-vetter-plus"
New-Item -ItemType Directory -Force "$d\scripts" | Out-Null
$b = "https://raw.githubusercontent.com/qiye2014/Seven-skills/main/skill-vetter-plus"
Invoke-WebRequest "$b/SKILL.md"              -OutFile "$d\SKILL.md"
Invoke-WebRequest "$b/scripts/scan_skill.py" -OutFile "$d\scripts\scan_skill.py"
Invoke-WebRequest "$b/sensitive_paths.txt"   -OutFile "$d\sensitive_paths.txt"
```

See [skill-vetter-plus/README.md](./skill-vetter-plus/README.md) for full documentation.
