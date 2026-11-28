---
name: citation-manager
description: 参考文献与引用管理工作流，按论断句定位插入引用、连锁更新编号、合并重复文献、在 GB/T 7714 与 APA 等格式间转换，并逐条核验引用真实性与正文—文后一致性，交付可编辑稿件和引用证据表。当用户要求插引用、补参考文献、重排编号、文献去重、统一参考文献格式或核对引用来源时使用。适用于期刊论文、学位论文、综述，支持中英文混排。
---

# 参考文献与引用管理：挂得对、编得顺、收得净、对得上

把真实稿件和真实文献库变成**可继续编辑、可逐条回查**的引用整理结果。核心不是“生成参考文献列表”，而是四个可验证的性质：**挂得对**（引用落在需要来源支撑的论断句上）、**编得顺**（插入/删除/调序后编号、交叉引用与文后列表同步）、**收得净**（同一文献的多种写法合并为一条并说明依据）、**对得上**（条目真实存在、元数据准确、论断与文献结论匹配）。

## 何时使用

- 需要在稿件中插入或调整引用，并说明为何该句需要来源支撑。
- 需要重排编号、同步正文标记与文后列表、处理合并或调序后的编号冲突。
- 需要识别中英文题名、预印本与正式版、不同数据库导出造成的重复条目。
- 需要转换参考文献格式、补齐 DOI/卷期页/文献类型等字段，或核验引用真实性。

不适用：无稿件或文献库材料、要求凭空编造文献或虚构 DOI 的场景。

## 运行环境与输出路径（重要）

- 平台把本 Skill 安装到 `/skills/weekly-skill`，用固定案例运行。先读真实输入 `/input/case.json` 与 `/input/task.md`，`case.json` 中可能有 `case_id`、`output_contract`、稿件与文献库路径、目标规范；**以实际字段为准，不从标签或文件名推断材料内容**。
- 中间文件写在 `/app/work`，不要污染输入目录；资源从 `/skills/weekly-skill/resources/` 读取。
- 最终产物写到 `/app/output/result.json`（UTF-8 合法 JSON），并同时保存**可编辑稿件** `/app/output/manuscript_edited.md` 与**同步文献表** `/app/output/reference_list.md` 供复核。
- `result.json` 必须原样回填 `case_id`，并完整包含 `output_contract` 的全部字段（不得改名、不得遗漏），再补充本 Skill 的扩展字段；若合同字段与本表同名，以合同为准。
- 预算内**尽早写入诚实的部分结果**再增量完善；3 个案例、每条件 3 次运行由平台安排，参赛者不提供测试案例或白板。
- 禁止提交预制答案、正式案例答案、假造的运行日志或评测成绩；本 Skill 包内不应含任何 `result.json`。

## 输入输出

输入：稿件文本或路径、文献库文本或路径（BibTeX / RIS / EndNote / CNKI 导出 / 纯文本）、目标格式规范与特殊约束。

输出：`result.json` 字段如下（`output_contract` 优先）：

| 字段 | 要求 |
|---|---|
| case_id | 从 case.json 原样回填；确实没有才填 `N/A` |
| status | `success` / `partial` / `unable` / `refused`；部分完成须说明未完成范围与人工接管位置 |
| manuscript | 完整可编辑稿件（保留原段落编号，含插入/更新后的引用标记），不省略、不以“建议”代替正文 |
| citation_actions | 数组，每项含 `action_id` / `type`（insert / renumber / dedupe / format / verify）/ `before` / `after` / `reason` / `anchor` / `evidence`；每处改动可独立复核 |
| reference_list | 数组，每项含 `ref_id` / `authors` / `year` / `title` / `venue` / `doi` / `type` / `normalized_key` / `source` / `verified`；元数据缺失填“原文未述”，不猜 |
| citation_map | 数组，每项含 `citation_id` / `claim` / `ref_id` / `position`（anchor）/ `match_basis` / `evidence` / `confidence`（high/medium/low） |
| verification | 对象，逐项给 `result`（pass/fail/na）与 `evidence`（含具体计数或抽查片段）：`placement_precision`、`numbering_continuity`、`dedupe_correctness`、`format_completeness`、`source_validity`、`claim_ref_match`、`coverage`、`no_new_facts` |
| uncertainties | 需人工确认、元数据冲突、DOI 无法解析、条目歧义、材料缺失等条目及原因 |
| sources | 使用的输入文件与页码/段号范围，界定输入边界 |
| change_log | 自检回修记录：问题、修正、位置 |

**锚点格式**：`p<页>:<段>` / `<章节>:<段>` / `fig<号>` / `tab<号>` / `eq<号>` / `ref:<ref_id>`，必须指向原文或文献库的真实位置。

## 工作流

### 第 1 步：建立输入清单与规则表
打开并读取稿件与文献库的实际文件，记录段落数、章节、文献条目数、导出字段与目标规范到 `sources`。从 task.md / case.json 抽取目标格式、引用样式（顺序编码制/著者—出版年制/脚注）、禁止改动项，形成本轮**规则表**，后续每步重读。文件缺失或不可读 → `status: unable` 并写明路径。

### 第 2 步：论断级引用定位（挂得对）
逐句识别哪些是需来源支撑的论断（数据、他人结论、方法来源、争议性判断），把引用插到**该论断所在句**而非段末或图注附近；一句多引和多句一引分别记录到 `citation_actions`。每条 `citation_map` 写明 `match_basis`：所引文献的主题、结论或数据为何能支撑该论断；证据不足的句子写入 `uncertainties`，不强行配文献。

### 第 3 步：编号与交叉引用连锁更新（编得顺）
按正文出现顺序维护引用序号字典：插入、删除、调序、章节合并后立即重排，同步修改正文标记、交叉引用、图表注与附录引用、文后列表序号。重排后逐号回扫“正文编号 ↔ 文后条目”一一对应，统计连续性与孤儿引用数量写入 `verification.numbering_continuity`，不得留下跳号或悬空编号。

### 第 4 步：条目归并、格式转换与来源核验（收得净、对得上）
- **去重**：按 DOI（最高优先）→ 题名归一化（大小写/标点/中英题名）→ 作者+年份+venue 建立 `normalized_key`；预印本与正式版、期刊与会议版本、不同数据库字段差异归为一条，并在 `change_log` 写明合并依据。同名作者的不同文献不得误合并，歧义写入 `uncertainties`。
- **格式转换**：按目标规范补齐作者、年份、题名、venue、卷期页、DOI、文献类型标识；中英文混排标点按规范统一，字段缺失标注“原文未述”。
- **来源核验**：可用的 DOI 或数据库信息逐条核对，标记 `verified` 为 true/false/unchecked；无法核验不得写成“已核实”。

### 第 5 步：三重自检与回修（关键）

**先跑机械核验，再做人工判断**——编号是否连续、正文与列表是否一一对应、是否有重复条目，这些完全可以机械核对：

```bash
R=/skills/weekly-skill/resources/scripts/ref_lint.py
# 正文与列表在同一文件（含 References / 参考文献 标题）
python3 "$R" check --single /app/work/manuscript.md --out /app/work
# 或分开两个文件
python3 "$R" check --body /app/work/draft.md --refs /app/work/references.md --out /app/work
cat /app/work/ref_report.md
```

| 报告项 | 含义 | 动作 |
|---|---|---|
| `dangling_citation` | 正文引用了列表里没有的编号 | **必须修**：补条目或改编号（这是最严重的错误） |
| `uncited_entry` | 列表有条目正文未引 | 评估：属于关键工作则补引，否则从列表删除 |
| `numbering_gap` | 编号跳号 | 按顺序编码制重排，并同步正文全部编号 |
| `numbering_duplicate` | 参考文献**列表内**同一编号被定义两次（如两条都标 `[2]`） | 核对是否重复条目，合并后重排 |
| `repeated_citations`（提示项，不计入问题数） | 正文多次引用同一编号 | 属正常学术写法，不需修改；仅用于核对引用密度 |
| `order_mismatch` | 首次引用顺序与列表编号不一致 | 顺序编码制下必须一致：按首次出现重排 |
| `duplicate_entry` | 条目题名高度相似（≥0.86） | 用 `merge` 子命令取候选，确认同一文献后合并并记依据 |
| `metadata_missing` | 缺作者或年份 | 补齐；原文确实没有则标 `原文未述` 并进 uncertainties |
| `style_inconsistent` | 部分条目有 DOI/年份、部分没有 | 统一风格：要么全补，要么统一省略并说明 |
| `cite_placement` | 同一处堆叠 4 个以上引用 | 确认是否每个论断都有对应来源，避免"整段末尾堆引用" |

疑似重复条目取归并候选（**不自动合并**，预印本/正式版/中英题名需看 DOI 与卷期判断）：
```bash
python3 "$R" merge --single /app/work/manuscript.md --out /app/work
```

**写出 result.json 后必须跑一次定位回查**——`check` 只保证编号自洽，发现不了"论断短引不在稿件里、证据短引不在文献库里、ref_id 指向不存在条目"这类致命错误：

```bash
python3 "$R" placement --manuscript /app/output/manuscript_edited.md \
                       --result /app/output/result.json \
                       --refs /app/output/reference_list.md --out /app/work
cat /app/work/placement_report.md
```

`placement_report.json` 给出 `claim_found_count` / `evidence_found_count` / `ref_resolved_count` / `anchor_ok_count` / `basis_ok_count`（分母均为 `citation_map_count`）。`claim_not_found_in_manuscript`、`evidence_not_found_in_references`、`ref_id_unresolved` 必须为 0；发现即回到第 2/4 步把论断、证据和编号改成真实可回查的原文短引，修完重跑。把五项计数原样写入 `verification.placement_precision` 与 `verification.claim_ref_match` 的 evidence，不得只写"通过"。

之后做脚本测不出的判断：引用是否真的挂在**需要来源支撑的那句论断**上（而非整段末尾）、正文论断与所引文献主题是否真的匹配、条目元数据是否与原文一致。

逐项核对 `resources/checklist.md`，把结果写入 `verification`（**优先用脚本计数**，不要只写“通过”）：
1. **覆盖**：需支撑论断句数 / 已配引用句数、文献库条目数 / 输出条目数、六类动作是否均有记录。
2. **回查**：抽查每条 `citation_map` 的 `anchor` 能否找到 `evidence` 短引；统计成功数 / 总数，失败即修正或降 confidence 并写入 `uncertainties`。
3. **一致性**：编号连续、正文—文后一一对应、去重无误并、元数据无新增事实、格式字段齐全。发现问题回到第 3/4 步修正并记入 `change_log`。
完成后 `status` 才能置 `success`；仍有未解决项则置 `partial` 并列出可人工接管位置。

### 第 6 步：输出可核验产物
写 `/app/output/result.json`、可编辑稿件与同步文献表；确认 `case_id` 已回填、`output_contract` 字段齐全、`verification` 含计数、`uncertainties` 与 `change_log` 如实填写。

## 异常处理

| 情况 | 处理 |
|---|---|
| 稿件/文献库缺失或编码混乱 | 写明具体路径与位置，`status: unable` 或 `partial`，不猜内容 |
| DOI 解析失败、条目查不到原文 | `verified: unchecked`，写入 `uncertainties`，保留原元数据 |
| 条目歧义、同名作者 | 不合并，分列两条并写明歧义依据 |
| 编号冲突 / 孤儿引用 | 重排并记入 `change_log`；无法定位的写入 `uncertainties` |
| 目标格式未知 | 按稿件中出现最多的规范处理，并在 `uncertainties` 请求确认 |
| 超长输入 / 预算紧张 | 分块处理、save early，标注处理到哪一段，宁可 `partial` 也不编造 |

## 资源

- `resources/scripts/ref_lint.py`：**执行内核**。`check` 检出悬空引用、未引条目、编号跳号/重号、首次引用顺序不符、重复条目、元数据缺失、风格不一致与引用堆叠；`merge` 给出重复条目归并候选（不自动合并）；`placement` 回查 `citation_map` 的论断短引、证据短引、ref_id、锚点、匹配依据与置信度是否真实可回查。重号只统计参考文献列表内部重复，正文多次引用同一编号仅记为 `repeated_citations` 提示。`--out` 可传目录（写入约定文件名）或直接传文件名，两种写法都不会报错。纯标准库，无第三方依赖。
- `environment/resources.yaml`：资源清单、依赖、运行时与产物说明。
- `resources/checklist.md`：自检与计数清单。
- `resources/field_dict.md`：字段字典、锚点格式、去重判据与编号规则。
- `resources/citation_rules.md`：GB/T 7714—2015 与 APA 常用字段映射、去重与核验示例。
- `resources/output_example.json`：输出结构示意（非答案）。
- `examples/README.md`：最小调用示例。

## 最小示例（示意，非真实稿件）

```bash
R=/skills/weekly-skill/resources/scripts/ref_lint.py
python3 "$R" check --single /app/work/manuscript.md --out /app/work
python3 "$R" merge --single /app/work/manuscript.md --out /app/work
cat /app/work/ref_report.md
# 写出 result.json 与稿件后：
python3 "$R" placement --manuscript /app/output/manuscript_edited.md \
                       --result /app/output/result.json --refs /app/output/reference_list.md \
                       --out /app/work
cat /app/work/placement_report.md
```

示意输出（仅结构）：

```json
{"mode": "numeric", "entry_count": 42, "distinct_cited": 40, "dangling_count": 0,
 "uncited_count": 2, "numbering_gap_count": 0, "numbering_duplicate_count": 0,
 "order_mismatch_count": 0, "duplicate_group_count": 0, "metadata_missing_count": 1}
```

真正的结果必须来自本次实际运行，示意输出不得冒充正式案例答案。
