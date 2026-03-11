# write-article 技能包

深度文章写作技能，支持微信公众号 + 今日头条双版本输出，自带排版规范、事实核查流程、双平台标题建议。

输入 `/write-article <选题或观点>` 即可自动完成全流程。

---

## 目录结构

```
skills/write-article/
├── skill.md              # 技能主文件
├── style-guide.md        # 排版规范（通用，随 skill 走）
├── user-preferences.md   # 作者偏好（新设备需修改为自己的信息）
└── README.md             # 本说明文件
```

---

## 安装步骤

### 第一步：确定本地路径

将整个 `write-article/` 目录放到你的工作目录下。推荐位置：

| 系统 | 推荐路径 |
|------|---------|
| macOS | `~/winsurf/skills/write-article/` |
| Linux | `~/winsurf/skills/write-article/` |
| Windows | `C:\Users\你的用户名\winsurf\skills\write-article\` |
| OpenClaw（任意平台） | 同上，取决于宿主系统 |

### 第二步：安装 skill 主文件到 Claude commands

**macOS / Linux：**
```bash
cp ~/winsurf/skills/write-article/skill.md ~/.claude/commands/write-article.md
```

**Windows（PowerShell）：**
```powershell
Copy-Item "$HOME\winsurf\skills\write-article\skill.md" "$HOME\.claude\commands\write-article.md"
```

**OpenClaw：** 将 `skill.md` 内容复制到 OpenClaw 的 skill 安装入口（通常是 UI 界面的"添加技能"或 `/skills` 目录）。

### 第三步：修改 skill.md 中的路径（重要）

`skill.md` 第一步中有两行读取路径，**必须改为你机器上的实际绝对路径**：

```
# 原文（需要替换）
~/winsurf/skills/write-article/user-preferences.md
~/winsurf/skills/write-article/style-guide.md
```

**macOS 示例：**
```
/Users/yourname/winsurf/skills/write-article/user-preferences.md
/Users/yourname/winsurf/skills/write-article/style-guide.md
```

**Linux 示例：**
```
/home/yourname/winsurf/skills/write-article/user-preferences.md
/home/yourname/winsurf/skills/write-article/style-guide.md
```

**Windows 示例（注意用正斜杠，Claude Code 在 Windows 上也接受）：**
```
C:/Users/yourname/winsurf/skills/write-article/user-preferences.md
C:/Users/yourname/winsurf/skills/write-article/style-guide.md
```

同时修改输出路径（第四步中的保存目录）：
```
# 改为你实际的 writing 输出目录
/Users/yourname/winsurf/writing/          ← macOS
/home/yourname/winsurf/writing/           ← Linux
C:/Users/yourname/winsurf/writing/        ← Windows
```

> ⚠️ Claude Code 的文件读取工具**不支持 `~` 展开**，必须写完整绝对路径。

### 第四步：修改作者信息

编辑 `user-preferences.md`，将以下字段改为自己的信息：

```markdown
- 名字：你的名字
- 公众号：你的公众号名称
- 定位：你的账号定位
```

同时更新 `skill.md` 底部"固定结尾模块"中的作者介绍 HTML 和 Markdown。

### 第五步：验证

在 Claude Code 中输入：
```
/write-article 测试选题
```

skill 开始读取 `user-preferences.md` 和 `style-guide.md` 即成功。

---

## 各平台路径速查

| 场景 | user-preferences.md 路径示例 |
|------|----------------------------|
| macOS（用户名 john） | `/Users/john/winsurf/skills/write-article/user-preferences.md` |
| Linux（用户名 john） | `/home/john/winsurf/skills/write-article/user-preferences.md` |
| Windows（用户名 john） | `C:/Users/john/winsurf/skills/write-article/user-preferences.md` |
| OpenClaw on macOS | 同 macOS |
| OpenClaw on Windows | 同 Windows |

---

## 文件说明

| 文件 | 说明 | 新设备是否需要修改 |
|------|------|-----------------|
| `skill.md` | 技能主逻辑 | 需要：更新路径 + 固定结尾作者信息 |
| `style-guide.md` | 排版规范、标题公式、事实核查标准 | 不需要（通用规范） |
| `user-preferences.md` | 作者信息、选题方向、风格偏好 | 需要：填写自己的信息 |

---

## 常见问题

**Q：skill 说找不到文件**
A：检查 `skill.md` 第一步的路径是否为完整绝对路径，`~` 在此处无效。

**Q：Windows 路径用反斜杠还是正斜杠？**
A：Claude Code 在 Windows 上两种都支持，推荐用正斜杠 `/` 避免转义问题。

**Q：OpenClaw 安装后路径在哪？**
A：OpenClaw 运行在宿主系统上，路径规则与宿主系统（Windows/macOS/Linux）相同，找到 Claude commands 目录安装即可。
