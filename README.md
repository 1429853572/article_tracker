# Article Tracker — 统一论文追踪工作流

> 同时追踪 **arXiv 预印本** + **顶刊正式论文**，自动采集、去重、筛选、LLM 双语摘要、多通道推送。

---

## 核心功能

| 能力 | 说明 |
|------|------|
| 双源采集 | arXiv Atom Feed + Semantic Scholar（顶刊）→ OpenAlex（补充元数据） |
| 跨源去重 | DOI → arXiv ID → title 模糊匹配(0.85)，自动合并更完整字段 |
| 三源摘要补全 | Semantic Scholar → OpenAlex → Crossref fallback |
| LLM 双语摘要 | 英文+中文一段话总结 + 标题/摘要翻译（DeepSeek 等 OpenAI 兼容 API） |
| 四层筛选 | core / proxy / eco / noise，关键词驱动 |
| 九通道输出 | JSON / Markdown / PDF / 邮件 / GitHub Pages / Excel / HTML / Obsidian / Zotero |
| CI/CD 自动化 | GitHub Actions 每日定时（北京时间 07:00），支持手动触发 |
| 保底机制 | 筛选不足 10 篇时自动补足，FALLBACK 标记可区分 |

---

## Fork & Deploy（一分钟部署）

### 1. Fork 本仓库

点击右上角 **Fork** 按钮。

### 2. 配置 GitHub Secrets

进入你 Fork 的仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：

| Secret 名称 | 说明 | 必须 |
|-------------|------|:----:|
| `S2_API_KEY` | [Semantic Scholar API Key](https://www.semanticscholar.org/product/api#api-key-form)（免费申请） | **是** |
| `DS_API_KEY` | DeepSeek / SiliconFlow LLM API Key | 否（无则跳过 LLM） |
| `EMAIL_SENDER` | 发件邮箱（如 QQ 邮箱） | 否（无则跳过邮件） |
| `EMAIL_TO` | 收件邮箱（多个用逗号分隔） | 否 |
| `SMTP_PASS` | SMTP 授权码（非邮箱密码） | 否 |
| `OPENALEX_EMAIL` | OpenAlex 礼貌池邮箱（加速请求） | 否 |

### 3. 启用 GitHub Pages

**Settings** → **Pages** → **Source** 选择 **"GitHub Actions"**。

### 4. 启用 Workflow

**Actions** → **Paper Tracker Daily** → 点击 **Enable workflow**（Fork 默认禁用定时任务）。

### 5. 修改配置（可选）

编辑 `config.yaml`，换成你自己的：
- `arxiv.keywords` — 你关注的 arXiv 搜索关键词
- `arxiv.categories` — arXiv 学科分类
- `screening.core_keywords` / `proxy_keywords` / `eco_keywords` — 筛选分层
- `top_journal.watchlist` — 你关注的期刊列表

### 6. 触发首次运行

**Actions** → **Paper Tracker Daily** → **Run workflow**，约 15-30 分钟后检查邮箱和 GitHub Pages。

---

## 本地运行

### 安装

```bash
git clone https://github.com/<你的用户名>/article_tracker.git
cd article_tracker
pip install -e ".[all]"
```

### 配置环境变量

创建 `.env` 文件：

```bash
S2_API_KEY=your_s2_key
DS_API_KEY=your_deepseek_key
EMAIL_SENDER=your_email@qq.com
EMAIL_TO=target@example.com
SMTP_PASS=your_smtp_auth_code
OPENALEX_EMAIL=your_email@example.com
```

### 运行

```bash
# 追踪全部来源（arXiv + 顶刊）
article_tracker track --config config.yaml --source all

# 仅追踪 arXiv
article_tracker track --source arxiv

# 试运行（不产生输出文件）
article_tracker track --dry-run

# 校验配置文件
article_tracker validate
```

---

## 配置说明

配置文件为 `config.yaml`，所有配置项均有中文注释。核心配置：

```yaml
# arXiv 源
arxiv:
  categories: ["cs.CV", "cs.AI", "cs.LG", "cs.CL", "cs.RO"]
  keywords: ["3D reconstruction", "Gaussian splatting", "SLAM"]
  logic: "AND"           # category 组 AND keywords 组（组内都是 OR）
  max_results: 100

# 顶刊源
top_journal:
  watchlist:
    - name: "ACM Transactions on Graphics"
    - name: "IEEE Transactions on Robotics"

# 四层筛选
screening:
  core_keywords: ["3D reconstruction", "Gaussian splatting", "SLAM"]
  proxy_keywords: ["NeRF", "point cloud", "depth estimation"]
  eco_keywords: ["scene understanding", "robotics"]
  output_tiers: ["core", "proxy", "eco"]  # noise 不输出

# LLM 双语摘要
llm:
  enabled: true
  base_url: "https://api.deepseek.com"
  model: "deepseek-v4-flash"
  api_key_env: "DS_API_KEY"

# 保底机制
freshness:
  fallback_when_empty: true   # 不足 10 篇时补足
  fallback_top_n: 10
```

---

## 工作流数据流

```
采集(arXiv + S2) → 去重(DOI→arXiv ID→title) → 摘要补全(S2→OA→Crossref)
  → 代码链接补全 → 四层筛选(core/proxy/eco/noise) → LLM双语摘要+翻译
  → 九通道输出(JSON/MD/PDF/Email/GitHub Pages/Excel/HTML/Obsidian/Zotero)
```

---

## 项目结构

```
article_tracker/
├── cli.py              # CLI 入口，pipeline 编排
├── api.py              # FastAPI HTTP 接口
├── config/             # 配置加载 + Pydantic V2 schema + 迁移
├── models/             # Article + ResearchProfile
├── source/             # ArxivSource + TopJournalSource
├── collect/            # Collector 多源编排
├── dedup/              # SeenStore + Deduplicator
├── enrich/             # AbstractEnricher + CodeLinkEnricher + LLMEnricher
├── screen/             # TierClassifier 四层筛选
├── output/             # 九通道输出（含 ghpages + email 暗色主题）
├── schedule/           # GitHub Actions 调度
└── infra/              # http_client + retry + logging
```

---

## License

MIT
