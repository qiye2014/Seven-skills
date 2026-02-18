# write-article 技能包

这是一个面向 Claude Code（包括 OpenClaw 等部署版本）的**深度文章写作技能**。

安装后，输入 `/write-article <选题或观点>` 即可生成微信公众号 + 今日头条双版本深度文章。

---

## 技能说明

- **作者定位**：Seven，普通人效率研究所，AI 职场影响方向
- **输出内容**：每次同时生成公众号 HTML 版 + 今日头条 Markdown 版
- **核心特点**：自带事实核查流程、排版规范、固定结尾模块，开箱即用

---

## 安装方法（Claude 直接执行以下步骤）

### 步骤 1：确认技能目录存在

```bash
mkdir -p ~/.claude/commands
```

### 步骤 2：下载技能文件

```bash
curl -fsSL https://raw.githubusercontent.com/qiye2014/Seven-skills/main/write-article/skill.md \
  -o ~/.claude/commands/write-article.md
```

### 步骤 3：验证安装

```bash
ls ~/.claude/commands/write-article.md
```

看到文件存在即安装成功。

---

## 使用方法

安装完成后，在 Claude Code 中输入：

```
/write-article 你的选题或观点
```

例如：

```
/write-article OpenAI 最新发布的 GPT-5 对普通打工人意味着什么
```

Claude 会自动完成：搜集素材 → 确认角度 → 撰写双版本文章 → 事实核查清单 → 标题和封面图建议。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `skill.md` | 技能主文件，安装到 `~/.claude/commands/` 后即可使用 |
| `README.md` | 本说明文件 |

---

## 注意事项

- 本技能**不依赖任何本地文件**，所有风格规范已内嵌，可在任何机器上直接使用
- 文章输出会直接显示在对话中，如需保存为文件请自行复制或告知 Claude 保存到指定路径
- 如需修改作者信息或风格偏好，直接编辑 `~/.claude/commands/write-article.md` 中对应部分即可
