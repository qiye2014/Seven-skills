# get-hot-topics 技能包

一键拉取微博、知乎、36氪、IT之家等平台热榜，自动筛选 AI / 科技 / 职场相关话题，生成选题清单并推荐最值得写的内容。

配合 `/write-article` 使用，形成完整的「找选题 → 写文章」工作流。

---

## 依赖：DailyHotApi

本技能通过 [DailyHotApi](https://github.com/imsyy/DailyHotApi) 获取热榜数据。

**有两种方式使用：**

### 方式 A：用公共演示接口（无需部署，直接用）

技能默认使用 `https://api-hot.imsyy.top`，安装后即可使用，无需任何配置。

> 注意：公共接口为演示用途，稳定性不保证，建议长期使用的话自行部署。

### 方式 B：自己部署（推荐，稳定）

用 Docker 一行命令部署到你的云服务器：

```bash
docker run --restart always -p 6688:6688 -d imsyy/dailyhot-api:latest
```

部署后把技能文件里的 API 地址改成你自己的：

```bash
# 编辑技能文件
sed -i 's|https://api-hot.imsyy.top|http://你的服务器IP:6688|g' \
  ~/.claude/commands/get-hot-topics.md
```

---

## 安装方法

### 步骤 1：确认技能目录存在

```bash
mkdir -p ~/.claude/commands
```

### 步骤 2：下载技能文件

```bash
curl -fsSL https://raw.githubusercontent.com/qiye2014/Seven-skills/main/get-hot-topics/skill.md \
  -o ~/.claude/commands/get-hot-topics.md
```

### 步骤 3：验证安装

```bash
ls ~/.claude/commands/get-hot-topics.md
```

---

## 使用方法

```
/get-hot-topics
```

**带参数使用：**

```
/get-hot-topics 只看知乎和36氪
/get-hot-topics 只找AI裁员相关的
/get-hot-topics 今天有没有AI公司融资的新闻
```

**配合写文章：**

```
/get-hot-topics          ← 第一步：找选题
（看到推荐的话题后）
/write-article 话题标题   ← 第二步：直接写
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `skill.md` | 技能主文件 |
| `README.md` | 本说明文件 |
