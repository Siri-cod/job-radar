# Job Radar · 全网岗位精准雷达

自动从**公司官网招聘系统**和**免费公开岗位 API** 抓取岗位，按你的画像精准打分筛选，
只保留 7 天内发布的新岗位，生成可筛选的看板网页，并对 24 小时内的新岗位发邮件提醒。

## 当前画像（config.yaml 已按此配置）

| 维度 | 设定 |
|---|---|
| 方向 | AI / ML Engineer、Data Science、Data Analysis、Data Engineering（35 个职位关键词） |
| 职级 | 排除 senior / staff / principal / lead / manager / architect / 实习 / werkstudent 等 30 类 |
| 语言 | **明确要求德语的岗位自动淘汰**（"德语加分"不算要求，会保留） |
| 经验 | **要求超过 3 年经验的岗位自动淘汰**（"3-5 years" 按下限 3 算，保留；"5+ years" 淘汰） |
| 地区 | 德国 + 欧洲 + 全球 Remote |

**全程免费**：GitHub Actions 跑抓取（公开仓库无限额度），GitHub Pages 托管看板。

---

## 覆盖的数据源（12 个，全部为官方公开接口）

**公司官网直连（最快最准，比招聘平台还早）**

| 系统 | 说明 |
|---|---|
| Greenhouse | 欧美科技公司主流 |
| Lever | 初创公司主流 |
| Ashby | 新一代初创公司 |
| SmartRecruiters | 大型企业 |
| Recruitee | 欧洲中型公司 |
| Personio | **德国中小企业主力** |
| Workday | SAP / Siemens / Zalando 等大厂 |

**免费公开聚合 API**

| 来源 | 说明 |
|---|---|
| Arbeitsagentur | **德国联邦劳工局官方 API，德国岗位覆盖最全** |
| Arbeitnow | 德国岗位 + 签证担保标记 |
| Remotive / RemoteOK / Himalayas | 全球远程岗位 |

**LinkedIn / StepStone / Indeed / Xing**
这几家的服务条款明确禁止抓取，技术上也有强反爬，硬爬会被封且不合规。
本项目改用两条稳妥路径：

1. 看板顶部生成**预置搜索链接**（已锁定"24 小时内 + 按时间排序"），一键直达；
2. 在这些平台开启**官方 Job Alert 邮件订阅**（见下方"补充设置"），进同一个邮箱。

---

## 部署（约 10 分钟，一次搞定）

### 1. 建仓库

在 GitHub 新建一个仓库（**建议设为 Public**，私有仓库 Actions 有分钟数限制），
把本文件夹全部内容推上去：

```bash
cd job-radar
git init && git add -A
git commit -m "init job radar"
git branch -M main
git remote add origin https://github.com/<你的用户名>/job-radar.git
git push -u origin main
```

### 2. 开启 GitHub Pages

仓库 → **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。

### 3. 允许 Actions 写仓库

仓库 → **Settings → Actions → General → Workflow permissions**
选 **Read and write permissions** → Save。

### 4. 配置邮件提醒（可选，但建议开）

Gmail 需要用「应用专用密码」，不是登录密码：
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)（需先开两步验证）。

仓库 → **Settings → Secrets and variables → Actions → New repository secret**，加 5 条：

| Name | Value |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `jan.bargallo.deike@gmail.com` |
| `SMTP_PASS` | 上一步生成的 16 位应用专用密码 |
| `MAIL_TO` | `jan.bargallo.deike@gmail.com` |

### 5. 跑起来

仓库 → **Actions → Job Radar → Run workflow** 手动触发一次。
跑完后看板地址是 `https://<你的用户名>.github.io/job-radar/`。

之后每小时整点自动运行，无需干预。

---

## 日常使用

- **看板**：`https://<你的用户名>.github.io/job-radar/` —— 手机电脑都能开，绿色左边框 = 本次新发现，红色 24h 标记 = 一天内发布。
- **邮件**：24 小时内发布且首次发现的岗位会立刻推到你邮箱，带直达投递按钮。同一岗位不会重复提醒（`data/seen.sqlite` 记录去重指纹）。

## 两条硬性规则怎么实现的

这两条用关键词列表做不可靠，所以写成了正则（`src/requirements_filter.py`），并配了单元用例：

**德语要求识别** —— 只匹配"把德语当能力要求"的表述，`Deutschland`、`Deutsche Bahn` 这类不会误伤：

| 判定要求德语（淘汰） | 判定不要求（保留） |
|---|---|
| Sehr gute Deutschkenntnisse | German is a plus |
| Verhandlungssicheres Deutsch | Deutsch ist von Vorteil |
| Fluent German required | No German required |
| German language skills at C1 | Berlin, Deutschland |
| Business level German | English is our working language |

**经验年限抽取** —— 取岗位声明的**下限**，且要求上下文里有 experience / Erfahrung 才算数：

| 原文 | 抽取 | 结果 |
|---|---|---|
| 3-5 years of experience | 3 | 保留 |
| 5+ years of professional experience | 5 | 淘汰 |
| Mindestens 4 Jahre Berufserfahrung | 4 | 淘汰 |
| 0-2 years, graduates welcome | 不设限 | 保留 |
| We have 20 years of company history | 无（非经验语境） | 保留 |

**担心过滤太狠？** 每次运行会写 `data/rejected.json`，列出被硬性条件淘汰的岗位和具体原因，
翻一眼就知道该不该放宽 `max_years_experience` 或关掉 `exclude_german_required`。

> 注意：部分数据源（Arbeitsagentur、SmartRecruiters）不返回职位正文，这类岗位无法判断德语/年限。
> 默认按 `keep_when_description_missing: true` 保留（宁可多看几个也不漏），
> 想要绝对干净就改成 `false`。

## 调精准度

只改 `config.yaml`，提交后自动重跑：

| 字段 | 作用 |
|---|---|
| `titles_any` | 职位标题必须命中其一，**这是筛选的第一道闸** |
| `titles_exclude` | 标题黑名单，过滤掉不符职级（senior/lead/实习等） |
| `keywords_boost` | 正文命中就加分，权重自己定 |
| `keywords_exclude` | 正文命中直接丢弃 |
| `locations` | 国家 / 城市 / 是否接受远程 |
| `requirements.max_years_experience` | 经验年限上限，当前 3 |
| `requirements.exclude_german_required` | 是否淘汰要求德语的岗位，当前开启 |
| `filters.min_score` | 分数门槛，当前 20。**漏岗位就调低，噪音多就调高** |
| `filters.freshness_days` | 只看几天内发布的 |
| `filters.alert_window_hours` | 多新的岗位才发邮件 |

加目标公司改 `companies.yaml`，从公司招聘页 URL 里抄 slug 即可（文件里有说明）。

## 调抓取频率

`.github/workflows/fetch.yml` 里的 cron：

```yaml
- cron: "0 * * * *"       # 每小时（默认）
- cron: "*/30 * * * *"    # 每 30 分钟
- cron: "0 7,13,19 * * *" # 每天 3 次
```

## 本地调试

```bash
pip install -r requirements.txt
python -m src.main --dry-run                    # 不发邮件
python -m src.main --dry-run --only greenhouse  # 只测单个数据源
open docs/index.html
```

---

## 补充设置：把平台的官方订阅也导进来

在这几个平台各建 1~2 个 Job Alert，频率选 **Daily / 即时**，收件邮箱用同一个：

- **LinkedIn** — 搜索后点 "Create job alert"，Date posted 选 Past 24 hours
- **StepStone** — 搜索页右侧 "Jobs per E-Mail"
- **Indeed** — 搜索页底部 "Get new jobs for this search by email"
- **Xing** — 搜索后 "Suchagent anlegen"

这样官网直连（本程序）+ 平台订阅（邮件）两条腿走路，覆盖率接近全网，且完全合规。
